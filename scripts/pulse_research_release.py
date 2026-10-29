"""Create review-only, versioned Hebrew research PDFs without modifying approved data.

Prepares a complete release *proposal* in an isolated directory. Only a
subsequent authenticated, protected human GitHub PR merge may publish files;
this CLI never changes main, pulse-data, official price targets or old PDFs.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from ai_research_packets import build_all
from ai_analyst_review_contract import validate_ai_proposal
from pulse_ai_full_research import SECTIONS,validate_full_research
from pulse_ai_research_drafts import canonical

ROOT=Path(__file__).resolve().parent.parent
HEADINGS={
 "financialResults":"תוצאות פיננסיות","growthDrivers":"מנועי הצמיחה",
 "profitability":"רווחיות","cashFlow":"תזרים מזומנים",
 "balanceSheet":"מאזן וחוב","riskChanges":"שינויים בסיכונים",
 "catalysts":"זרזים ואירועים","thesisComparison":"השפעה על התזה",
 "forecastSensitivity":"רגישות תחזיות","valuationMethodology":"מתודולוגיית השווי"
}
SAFE_ROOT="public/approved-research"
APPROVED_STORE="public/data/approved-research-versions.json"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def validate_unapproved_source(draft,packet):
    if not isinstance(draft,dict) or not isinstance(packet,dict):
        raise ValueError("Full immutable draft and source packet required")
    checksum=draft.get("immutableSha256")
    if not isinstance(checksum,str) or not re.fullmatch("[a-f0-9]{64}",checksum):
        raise ValueError("Missing immutable draft SHA")
    body={k:v for k,v in draft.items() if k!="immutableSha256"}
    if sha(canonical(body).encode())!=checksum:
        raise ValueError("AI draft was mutated after archival")
    if (draft.get("companyId")!=packet.get("companyId") or
        draft.get("sourcePacketSha256")!=packet.get("contentSha256") or
        draft.get("publicationStatus")!="not-approved" or
        draft.get("reviewStatus")!="not-approved" or
        draft.get("status")!="requires-human-review" or
        draft.get("proposedValuationAction")!="no-automatic-change" or
        draft.get("approvedTargetPrice") is not None or
        draft.get("approvedScenarios") is not None):
        raise ValueError("Unverified, mismatched, or self-approved source")
    full=draft.get("fullResearch")
    if not isinstance(full,dict) or full.get("contractVersion")!=2:
        raise ValueError("Requires complete research v2; cannot publish excerpts")
    if set(full)!={"contractVersion","headline","executiveSummary","sections","limitations","confidence","citedEvidenceCount","notice"}:
        raise ValueError("Unrecognized full research fields")
    if full["citedEvidenceCount"]!=len(draft.get("evidenceCitations",[])):
        raise ValueError("Citation count mismatch")
    # Recheck evidence against the current source packet rather than assuming
    # a public JSON's claim of 'AI executed' is an authentication credential.
    review={"version":1,"companyId":packet["companyId"],
            "packetContentSha256":packet["contentSha256"],
            "status":"requires-human-review","analysisMode":"model-generated-unverified",
            "evidenceCitations":draft["evidenceCitations"],
            "analystQuestions":draft["analystQuestions"],
            "interpretations":draft["interpretations"],
            "suggestedScenarioReview":draft["suggestedScenarioReview"],
            "proposedValuationAction":"no-automatic-change"}
    validate_ai_proposal(packet,review,model_execution_attested=True)
    for key in SECTIONS:
        s=full["sections"].get(key)
        if not isinstance(s,dict) or set(s)!={"summary","interpretation","evidenceIds","unknowns"}:
            raise ValueError("Invalid report section")
        if any(e not in {c["evidenceId"] for c in draft["evidenceCitations"]}
               for e in s["evidenceIds"]):
            raise ValueError("Unsupported source evidence")
    return full

def registry_company(packet):
    registry=json.loads((ROOT/"public/data/official-registry.json").read_text(encoding="utf-8"))
    matches=[c for c in registry["companies"] if c["id"]==packet["companyId"]]
    if len(matches)!=1:raise ValueError("Company absent from official registry")
    return matches[0]

def validate_current_approved(store):
    """Metadata-only sidecar: cannot silently migrate existing approved models."""
    if not isinstance(store,dict) or store.get("version")!=1:
        raise ValueError("Unrecognized historical approved-research store")
    if not isinstance(store.get("versions"),list) or not isinstance(store.get("activeByCompany"),dict):
        raise ValueError("Malformed approved history")
    by_id={}
    for item in store["versions"]:
        if not isinstance(item,dict) or not re.fullmatch(r"research-v:[a-f0-9]{32}",str(item.get("id"))):
            raise ValueError("Untrusted previous release")
        body={k:v for k,v in item.items() if k!="immutableSha256"}
        if item.get("immutableSha256")!=sha(canonical(body).encode()):
            raise ValueError("Historical release was edited")
        if item["id"] in by_id:raise ValueError("Duplicate version")
        by_id[item["id"]]=item
        pdf=item.get("pdfPath","")
        if not isinstance(pdf,str) or not pdf.startswith(SAFE_ROOT+"/") or ".." in Path(pdf).parts:
            raise ValueError("Invalid versioned PDF path")
        if not re.fullmatch("[a-f0-9]{64}",str(item.get("pdfSha256"))):
            raise ValueError("Missing PDF provenance")
    for cid,version in store["activeByCompany"].items():
        if version not in by_id or by_id[version].get("companyId")!=cid:
            raise ValueError("Published pointer mismatch")
    return store

def pack_version(packet,draft,current_store,*,as_of:str):
    """Make a release PROPOSAL; do NOT advance an existing active pointer."""
    full=validate_unapproved_source(draft,packet)
    current=validate_current_approved(current_store)
    date=dt.datetime.fromisoformat(as_of.replace("Z","+00:00"))
    if date.tzinfo is None:raise ValueError("Timezone-aware approval proposal date required")
    date=date.astimezone(dt.timezone.utc).isoformat()
    company=registry_company(packet)
    id_seed=canonical({"companyId":packet["companyId"],"sourceSha":packet["contentSha256"],
                      "draftSha":draft["immutableSha256"],"type":"proposed-pending-human-review"})
    vid="research-v:"+sha(id_seed.encode())[:32]
    if any(v["id"]==vid for v in current["versions"]):
        raise ValueError("Proposal already exists in approved archive")
    slug=re.sub("[^A-Za-z0-9_-]","-",packet["ticker"]).strip("-")[:72]
    if not slug:raise ValueError("Unsafe ticker path")
    path=f"{SAFE_ROOT}/{slug}/{vid[11:]}.pdf"
    version={
      "id":vid,"companyId":packet["companyId"],"ticker":packet["ticker"],
      "sourcePacketSha256":packet["contentSha256"],"draftSha256":draft["immutableSha256"],
      "proposalCreatedAt":date,"parentVersionId":current["activeByCompany"].get(packet["companyId"]),
      "pdfPath":path,
      "publicationStatus":"proposed-awaiting-authenticated-merge",
      "researchHeadline":full["headline"],"confidence":full["confidence"],
      "approvedTargetChanged":False,"approvedScenarioWeightsChanged":False,
      "legacyModelMigration":"not-performed",
      "ownerReview":"required",
      "sourceReferenceCount":len(draft["evidenceCitations"]),
    }
    return full,version

def render_hebrew_pdf(full,version,outfile,*,simulation=False):
    """ReportLab + installed DejaVu font + bidi. No download/external API."""
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from bidi.algorithm import get_display
    font=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if not (font.is_file() and bold.is_file()):
        raise ValueError("DejaVu Unicode fonts missing; refuse corrupt Hebrew PDF")
    for name,fn in (("PulseHebrew",font),("PulseHebrewBold",bold)):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name,str(fn)))
    outfile=Path(outfile)
    if outfile.exists():raise ValueError("Version PDF already exists: cannot overwrite")
    outfile.parent.mkdir(parents=True,exist_ok=True)
    from reportlab.lib.colors import HexColor
    w,h=595.28,841.89
    doc=canvas.Canvas(str(outfile),pagesize=(w,h),pageCompression=1,invariant=1)
    doc.setTitle("PULSE | Research proposal awaiting owner approval")
    doc.setAuthor("PULSE Investment Research")
    bg=HexColor("#111d2b");text=HexColor("#e5f5f5");muted=HexColor("#bdcfd9");teal=HexColor("#6ee5ca")
    y=0;page=0
    def new_page():
        nonlocal y,page
        if page:doc.showPage()
        page+=1
        doc.setFillColor(bg);doc.rect(0,0,w,h,stroke=0,fill=1)
        doc.setFillColor(teal);doc.setFont("PulseHebrewBold",11);doc.drawString(42,h-43,"PULSE  /  RESEARCH REVIEW")
        doc.setStrokeColor(HexColor("#42616a"));doc.line(42,h-55,w-42,h-55)
        doc.setFont("PulseHebrew",9);doc.setFillColor(muted)
        doc.drawString(42,27,f"PROPOSAL ONLY   ·   page {page}")
        y=h-89
    def lines(value,maxwidth,fontname,sz):
        # Logical words are fitted before bidi display to avoid splitting RTL
        # graphemes and English tickers/numerals incorrectly.
        out=[]
        for para in str(value).splitlines() or [""]:
            acc=""
            for word in para.split():
                test=(acc+" "+word).strip()
                if acc and pdfmetrics.stringWidth(get_display(test),"PulseHebrew",sz)>maxwidth:
                    out.append(acc);acc=word
                else:acc=test
            out.append(acc)
        return out
    def paragraph(value,*,sz=10,leading=18,is_title=False,color=None):
        nonlocal y
        face="PulseHebrewBold" if is_title else "PulseHebrew"
        for line in lines(value,w-88,face,sz):
            if y<74:new_page()
            doc.setFillColor(color or text);doc.setFont(face,sz)
            doc.drawRightString(w-44,y,get_display(line))
            y-=leading
        y-=6
    new_page()
    paragraph("טיוטת מחקר לאישור — אין שינוי במחיר יעד",sz=16,leading=26,is_title=True,color=teal)
    if simulation:paragraph("TEST / MOCK — דוח בדיקה בלבד, ללא ניתוח AI אמיתי",sz=11,is_title=True,color=HexColor("#efc688"))
    paragraph(full["headline"],sz=14,leading=23,is_title=True)
    paragraph(full["executiveSummary"],sz=11,leading=20)
    paragraph("פרטי מקור",sz=12,leading=19,is_title=True,color=teal)
    paragraph(f"{version['ticker']} · SHA256 {version['sourcePacketSha256'][:20]}…",sz=9,leading=16)
    paragraph("אישור נדרש דרך GitHub PR מוגן. המסמך אינו המלצה מאושרת.",sz=9,leading=16,color=HexColor("#efc688"))
    for section in SECTIONS:
        y-=5
        paragraph(HEADINGS[section],sz=12,leading=20,is_title=True,color=teal)
        info=full["sections"][section]
        paragraph(info["summary"],sz=10)
        paragraph("השלכות לבדיקה: "+info["interpretation"],sz=10)
        if info["unknowns"]:paragraph("פערי מידע: "+"; ".join(info["unknowns"]),sz=9,color=muted)
        if info["evidenceIds"]:
            paragraph("מזהי מקורות: "+", ".join(info["evidenceIds"]),sz=8,color=muted)
    if full["limitations"]:
        paragraph("מגבלות ונתונים חסרים",sz=12,is_title=True,color=teal)
        for item in full["limitations"]:paragraph("• "+item,sz=9,color=muted)
    doc.save()
    data=outfile.read_bytes()
    if not data.startswith(b"%PDF") or len(data)<2400:
        raise ValueError("PDF output invalid")
    return sha(data),len(data),page

def build_proposal_files(packet,draft,current_store,outdir,*,as_of,simulation=False):
    outdir=Path(outdir)
    if outdir.exists() and any(outdir.iterdir()):
        raise ValueError("Output staging must be empty; never overwrite")
    full,version=pack_version(packet,draft,current_store,as_of=as_of)
    pdf=outdir/version["pdfPath"]
    digest,bytecount,pages=render_hebrew_pdf(full,version,pdf,simulation=simulation)
    version["pdfSha256"]=digest
    version["pdfBytes"]=bytecount
    version["pdfPages"]=pages
    version["immutableSha256"]=sha(canonical(version).encode())
    # This is a *candidate* index, staged only. A trusted protected PR merge
    # must approve and explicitly release it; this function never promotes.
    staged={
      "version":1,"proposalOnly":True,"candidateVersion":version,
      "currentApprovedVersion":current_store["activeByCompany"].get(packet["companyId"]),
      "releaseAuthority":"human-protected-github-pr-merge-required",
      "simulation":simulation,"pdfSha256":digest,
      "publishAutomatically":False
    }
    meta=outdir/"release-proposal.json"
    meta.write_text(json.dumps(staged,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return staged

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",required=True)
    p.add_argument("--draft-id",required=True)
    p.add_argument("--draft-store",required=True)
    p.add_argument("--approved-store",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--simulate",action="store_true")
    a=p.parse_args()
    output=Path(a.output).resolve()
    if output==ROOT or output.is_relative_to(ROOT/"public") or output.is_relative_to(ROOT/"src"):
        raise ValueError("Proposal files must be outside published repository areas")
    packets=build_all()
    packet=packets[a.ticker]
    drafts=json.loads(Path(a.draft_store).read_text(encoding="utf-8"))
    eligible=[d for d in drafts["drafts"] if d["id"]==a.draft_id]
    if len(eligible)!=1:raise ValueError("Exactly one immutable source draft required")
    approved=json.loads(Path(a.approved_store).read_text(encoding="utf-8"))
    result=build_proposal_files(packet,eligible[0],approved,output,
                               as_of=dt.datetime.now(dt.timezone.utc).isoformat(),
                               simulation=a.simulate)
    print(json.dumps({"proposalOnly":True,"simulation":a.simulate,
                       "proposalId":result["candidateVersion"]["id"],
                       "pdfSha256":result["pdfSha256"],"approvedChanged":False,
                       "paidAiExecuted":False}))
if __name__=="__main__":main()
