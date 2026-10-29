"""Generate a visibly labelled, reproducible META research preview PDF only.

Uses real source-bound META packet and MockAIProvider. Never creates or alters
an approved research record, and never passes off mock text as model findings.
"""
import json
from pathlib import Path
from ai_research_packets import build_all
from pulse_ai_full_research import validate_full_research
from pulse_ai_pipeline import MockAIProvider
from pulse_research_release import render_hebrew_pdf

def main():
    packet=build_all()["META"]
    doc=MockAIProvider().analyze(packet)
    result=validate_full_research(packet,doc,model_execution_attested=False)
    path=Path("work/release-preview/meta-q3-2026-TEST-MOCK.pdf")
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():path.unlink()  # local ephemeral fixture ONLY; no public PDFs.
    provenance={"ticker":"META","sourcePacketSha256":packet["contentSha256"]}
    sha,bytes,pages=render_hebrew_pdf(doc,provenance,path,simulation=True)
    print(json.dumps({"status":"mock-pdf-only","paidAiExecuted":False,
                      "approvedResearchChanged":False,"path":str(path),
                      "pdfSha256":sha,"pages":pages,"sizeBytes":bytes,
                      "sourceEvidenceCitations":result["cited"]}))
if __name__=="__main__":main()
