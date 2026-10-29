"""No-cost providers and source-checked pre-API end-to-end replay.

The mock provider is intentionally forbidden from producing a
model-generated-unverified or approved result. No fake paid results enter
public/data. An OpenAI provider requires the separate opt-in private runner.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from ai_analyst_review_contract import validate_ai_proposal
from pulse_ai_full_research import SECTIONS,LIMITATION_TEXT,validate_full_research
from ai_research_packets import build_all
from pulse_ai_analysis_queue import ROOT, build_queue, validate, utc_at

class MockAIProvider:
    name="mock-simulation-no-model"
    def analyze(self,packet):
        observations=packet.get("financialObservations",[])
        reviews=packet.get("research",{})
        official=packet.get("latestIssuerResearch") or {}
        issuer_metrics=official.get("sourceBoundMetrics",[])
        if issuer_metrics:
            first=issuer_metrics[0]
            evidence="issuer-metric:"+packet["companyId"]+":"+first["metricId"]
            citations=[{"evidenceId":evidence,"kind":"issuer-report-metric",
                        "claim":"בדיקת MOCK: בדוח הרשמי נמצא מדד "+first["metricId"]+".",
                        "uncertainty":"נתון רשמי שנקלט, אך פירושו הפיננסי דורש בדיקת אנליסט."}]
            interpretations=[{"observation":"נמצא מדד בדוח המנפיק החדש.",
                "hypothesis":"יש לבדוק את ההשפעה של המדד על התחזית הקודמת.",
                "evidenceIds":[evidence],
                "unknowns":["לא בוצע ניתוח מודל AI","אין שינוי אוטומטי בשווי"]}]
        elif observations:
            first=observations[0]
            evidence=first["observationId"]
            kind="financial-observation"
            label=str(first.get("metricId") or "reported-metric")
            citation={"evidenceId":evidence,"kind":kind,
                      "claim":"בדיקת MOCK: מקור מקושר למדד "+label+". אין זו מסקנת השקעה.",
                      "uncertainty":"מקור ונתון טרם אושרו על ידי אנליסט."}
            interpretation={"observation":"הדוח מציג מדד שדורש הצלבה.",
                            "hypothesis":"מומלץ לבחון האם המדד תואם לתקופות קודמות.",
                            "evidenceIds":[evidence],
                            "unknowns":["אין הרצת מודל AI","ההשפעה על השווי לא נבדקה"]}
            citations=[citation]
            interpretations=[interpretation]
        elif (reviews or {}).get("sections"):
            name=next(iter(reviews["sections"]))
            evidence="research-section:"+name
            citations=[{"evidenceId":evidence,"kind":"research-section",
                        "claim":"בדיקת MOCK: נמצא מקטע מחקר שמחייב בדיקה.",
                        "uncertainty":"מסמך אנליסט לא מאומת כדוח מנפיק"}]
            interpretations=[{"observation":"קיים מחקר קודם לבדיקה.",
                              "hypothesis":"יש לוודא שכל שינוי בתזה נתמך בדוח רשמי.",
                              "evidenceIds":[evidence],"unknowns":["מודל AI לא הופעל"]}]
        else:
            citations=[];interpretations=[]
        primary=citations[0]["evidenceId"] if citations else None
        sections={}
        for section in SECTIONS:
            sections[section]={
                "summary":"TEST/MOCK בלבד — מידע זה נוצר בסימולציה מקומית, ללא מודל AI.",
                "interpretation":("יש להשוות את המקור לדוח הרשמי לפני הסקת מסקנות."
                                  if primary else LIMITATION_TEXT),
                "evidenceIds":[primary] if primary else [],
                "unknowns":["אין הפעלת מודל AI","אין אישור מחקר או מחיר יעד"]}
        return {"version":2,"companyId":packet["companyId"],
                "packetContentSha256":packet["contentSha256"],
                "status":"requires-human-review","analysisMode":"deterministic-no-ai",
                "headline":"TEST/MOCK — הדגמת זרימת מחקר, לא ניתוח השקעה",
                "executiveSummary":"סימולציית מחקר להוכחת קליטה, אימות, תור וטיוטה. לא הופעל מודל בתשלום.",
                "sections":sections,"evidenceCitations":citations,
                "analystQuestions":["Mock בלבד: האם המדדים תואמים לדוח הרשמי ולהנחות הקודמות?"],
                "suggestedScenarioReview":[],"targetPriceProposal":None,
                "proposedValuationAction":"no-automatic-change",
                "limitations":["לא הופעל OpenAI API","אין מסקנת הערכת שווי אמיתית"],
                "confidence":"low"}

class OpenAIProvider:
    """Guarded provider bridge; deliberately never called by replay or CI."""
    name="openai-responses-private-gated"
    def analyze(self,*args,**kwargs):
        raise RuntimeError("Paid execution is disabled in pre-API replay. Use the separate guarded private runner only after owner activation.")

def simulate(queue,packets,ticker,now):
    """A complete local replay of queuing, mock analysis, validation and review.

    Preview results carry explicit MOCK labels and never mutate the queue or
    the published/approved research, PDF manifest or active target pointer.
    """
    jobs=[j for j in queue["jobs"] if j["ticker"]==ticker]
    current=queue.get("latestByCompany",{})
    jobs=[j for j in jobs if current.get(j["companyId"])==j["id"]]
    if len(jobs)!=1:raise ValueError("Expected one current source job for ticker")
    job=jobs[0]
    if job["status"]!="queued":
        raise ValueError("Report is blocked or not queued; no AI mock run")
    packet=packets[ticker]
    if packet["companyId"]!=job["companyId"]:
        raise ValueError("Packet company mismatch")
    sources=[o["sourceSha256"] for o in packet["financialObservations"]]
    issuer=(packet.get("latestIssuerResearch") or {}).get("report") or {}
    if (packet.get("latestIssuerResearch") or {}).get("sourceBoundMetrics"):
        sources.append(issuer.get("digest"))
    if job["sourceSha256"] not in sources:
        raise ValueError("Current source version has no financial observation in packet")
    model=MockAIProvider()
    proposal=model.analyze(packet)
    checked=validate_full_research(packet,proposal)
    if checked["modelChanges"]!=0:raise ValueError("Mock attempted a model change")
    return {"version":1,"simulation":True,"analysisMode":"mock-simulation-no-model",
            "paidAiExecuted":False,"authorizedBy":None,"publicationStatus":"not-approved",
            "approvedModelChanged":False,"ticker":ticker,"companyId":job["companyId"],
            "jobId":job["id"],"sourceSha256":job["sourceSha256"],
            "packetSha256":packet["contentSha256"],"createdAt":utc_at(now),
            "stages":["detected","validated","queued","mock-processing","mock-draft-ready","mock-pending-review"],
            "proposal":proposal,"validation":checked,
            "notice":"TEST/MOCK ONLY. No AI model, secret, approval, public publication or charge."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="META")
    p.add_argument("--output",default="work/pulse-ai-mock-preview.json")
    args=p.parse_args()
    dest=ROOT/args.output
    # Tests never deposit synthetic content in a public or tracked folder.
    if not dest.resolve(strict=False).is_relative_to((ROOT/"work").resolve(strict=False)):
        raise ValueError("Mock preview MUST remain under work/, not public/data")
    latest=json.loads((ROOT/"public/data/earnings-research-candidates.json").read_text(encoding="utf-8"))
    registry=json.loads((ROOT/"public/data/official-registry.json").read_text(encoding="utf-8"))
    previous_path=ROOT/"public/data/ai-analysis-queue.json"
    queue=json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else build_queue(latest,{},registry,dt.datetime.now(dt.timezone.utc).isoformat())
    validate(queue,registry)
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    result=simulate(queue,build_all(),args.ticker,now)
    dest.parent.mkdir(parents=True,exist_ok=True)
    # This is never pushed to pulse-data, checked in, or served in production.
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"mock-only","ticker":args.ticker,
                      "source":result["sourceSha256"],"stage":result["stages"][-1],
                      "paidAiExecuted":False,"approvedResearchChanged":False}))

if __name__=="__main__":main()
