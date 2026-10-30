"""Validate full ten-section, source-cited, unapproved research drafts.

External text is untrusted. The model's output never authenticates its own
execution or authorizes a target/portfolio/PDF update. Numeric financial
comparisons are calculated by existing deterministic modules, not this model.
"""
from __future__ import annotations
import hashlib
import json
from ai_analyst_review_contract import validate_ai_proposal

SECTIONS=("financialResults","growthDrivers","profitability","cashFlow","balanceSheet",
          "riskChanges","catalysts","thesisComparison","forecastSensitivity","valuationMethodology")
MODES=("model-generated-unverified","deterministic-no-ai")
ALLOWED_CONFIDENCE=("low","medium","high")
LIMITATION_TEXT="אין די מידע כדי להסיק מסקנה."

def nonblank(v,maxchars):
    return isinstance(v,str) and 0<len(v.strip())<=maxchars

def to_review_v1(packet,full):
    if not isinstance(full,dict) or set(full)!={
        "version","companyId","packetContentSha256","status","analysisMode",
        "headline","executiveSummary","sections","evidenceCitations",
        "analystQuestions","suggestedScenarioReview","targetPriceProposal",
        "proposedValuationAction","limitations","confidence"}:
        raise ValueError("Full research draft must contain the complete strict contract")
    if full["version"]!=2 or full["targetPriceProposal"] is not None or full["confidence"] not in ALLOWED_CONFIDENCE:
        raise ValueError("Full draft cannot carry an unapproved target price")
    if not nonblank(full["headline"],350) or not nonblank(full["executiveSummary"],4500):
        raise ValueError("Missing bounded research summary")
    sections=full["sections"]
    if not isinstance(sections,dict) or set(sections)!=set(SECTIONS):
        raise ValueError("Missing required financial research sections")
    if not isinstance(full["limitations"],list) or len(full["limitations"])>20 or not all(nonblank(x,2500) for x in full["limitations"]):
        raise ValueError("Missing bounded research limitations")
    interpretations=[]
    for label in SECTIONS:
        section=sections[label]
        if not isinstance(section,dict) or set(section)!={"summary","interpretation","evidenceIds","unknowns"}:
            raise ValueError("Malformed analytical section")
        if not nonblank(section["summary"],2500) or not nonblank(section["interpretation"],2500):
            raise ValueError("Empty analytical section")
        evidence=section["evidenceIds"]
        unknowns=section["unknowns"]
        if (not isinstance(evidence,list) or len(evidence)>20
            or not isinstance(unknowns,list) or len(unknowns)>10 or not all(nonblank(x,2500) for x in unknowns)):
            raise ValueError("Malformed financial analysis evidence and limitations")
        if evidence:
            interpretations.append({"observation":section["summary"],
                                    "hypothesis":section["interpretation"],
                                    "evidenceIds":evidence,"unknowns":unknowns})
        elif section["interpretation"]!=LIMITATION_TEXT or not unknowns:
            raise ValueError("Uncited analysis must explicitly state insufficient evidence")
    review={"version":1,"companyId":full["companyId"],
        "packetContentSha256":full["packetContentSha256"],
        "status":full["status"],"analysisMode":full["analysisMode"],
        "evidenceCitations":full["evidenceCitations"],
        "analystQuestions":full["analystQuestions"],
        "interpretations":interpretations,
        "suggestedScenarioReview":full["suggestedScenarioReview"],
        "proposedValuationAction":full["proposedValuationAction"]}
    return review

def validate_full_research(packet,full,*,model_execution_attested=False):
    review=to_review_v1(packet,full)
    validated=validate_ai_proposal(packet,review,model_execution_attested=model_execution_attested)
    if len(review["evidenceCitations"])==0 and full["confidence"]=="high":
        raise ValueError("High confidence cannot be assigned without source evidence")
    return {"valid":True,"sections":len(SECTIONS),
            "cited":validated["cited"],
            "interpretations":validated["interpretations"],
            "modelChanges":0,"status":"requires-human-review",
            "fullResearch":True}

def build_public_full_research_draft(packet,full,model,*,execution_attested=False):
    from pulse_ai_research_drafts import build_public_draft,canonical
    validate_full_research(packet,full,model_execution_attested=execution_attested)
    v1=to_review_v1(packet,full)
    base=build_public_draft(packet,v1,model,execution_attested=execution_attested)
    raw=hashlib.sha256(canonical(full).encode("utf-8")).hexdigest()
    base["id"]="ai-draft:"+hashlib.sha256((packet["companyId"]+"|"+packet["contentSha256"]+"|"+raw).encode()).hexdigest()[:32]
    base["proposalSha256"]=raw
    base["fullResearch"]={
        "contractVersion":2,"headline":full["headline"],
        "executiveSummary":full["executiveSummary"],
        "sections":full["sections"],"limitations":full["limitations"],
        "confidence":full["confidence"],
        "citedEvidenceCount":len(full["evidenceCitations"]),
        "notice":"AI-generated interpretation pending analyst review, not a verified investment target."
    }
    return base
