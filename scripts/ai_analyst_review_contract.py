"""Validate potential AI analyst OUTPUT, without invoking or trusting an AI.

No data mutation, no approval, no execution. All suggestions remain pending.
This schema deliberately separates cited evidence from interpretation.
"""
import hashlib
import json
import math
import re
from pathlib import Path

KINDS={"financial-observation", "archived-forecast", "research-section", "valuation-scenario"}
SCENARIOS={"bear","base","bull"}

def _str(v,maxlen=4000):
    return isinstance(v,str) and bool(v.strip()) and len(v)<=maxlen

def _type_is_safe(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)

def _validate_input_packet(packet):
    """Recalculate the source snapshot digest before accepting any model citation.

    A checksum binds the review to an exact packet; it is NOT a signature,
    an issuer attestation, or a substitute for protected GitHub approvals.
    """
    if not isinstance(packet, dict) or type(packet.get("contractVersion")) is not int or packet["contractVersion"] != 1:
        raise ValueError("AI packet missing or wrong contract")
    digest = packet.get("contentSha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid packet digest")
    unsigned = {key: value for key, value in packet.items() if key != "contentSha256"}
    try:
        serialized = json.dumps(unsigned, sort_keys=True, ensure_ascii=False,
                                separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("Invalid packet content") from exc
    calculated = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if calculated != digest:
        raise ValueError("Packet content changed without matching SHA-256")
    policy = packet.get("trustPolicy")
    if (not isinstance(policy, dict)
        or policy.get("mayModifyTargetsOrProbabilities") is not False
        or policy.get("includesPersonalPortfolio") is not False
        or policy.get("aiAnalysisExecuted") is not False):
        raise ValueError("Input packet trust gate is not locked")
    observations = packet.get("financialObservations")
    if not isinstance(observations, list):
        raise ValueError("Missing financial evidence")
    for ob in observations:
        if (not isinstance(ob, dict) or ob.get("modelEligible") is not False
            or ob.get("verification") not in ("pending-review", "needs-reconciliation")
            or ob.get("reviewStatus") not in ("pending-review", "needs-reconciliation")
            or not isinstance(ob.get("sourceSha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", ob["sourceSha256"])):
            raise ValueError("Unreviewed accounting evidence cannot be promoted")
    return digest


def _evidence_candidates(packet):
    """Index unique, typed evidence IDs; never let one source shadow another."""
    candidates = {}

    def add(evidence_id, kind):
        if (not isinstance(evidence_id, str) or not evidence_id.strip()
            or len(evidence_id) > 256):
            raise ValueError("Invalid evidence identifier")
        if evidence_id in candidates:
            raise ValueError("Ambiguous duplicate evidence identifier")
        candidates[evidence_id] = kind

    for row in packet["financialObservations"]:
        add(row.get("observationId"), "financial-observation")
    forecasts = packet.get("archivedForecasts")
    if not isinstance(forecasts, list):
        raise ValueError("Malformed archived forecast evidence")
    for row in forecasts:
        if not isinstance(row, dict):
            raise ValueError("Malformed archived forecast evidence")
        add(row.get("id"), "archived-forecast")
    research = packet.get("research")
    if research is not None:
        if not isinstance(research, dict) or not isinstance(research.get("sections"), dict):
            raise ValueError("Malformed research evidence")
        for name in research["sections"]:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Invalid research section identifier")
            add("research-section:" + name, "research-section")
    model = packet.get("valuationModel")
    if model is not None:
        if not isinstance(model, dict) or not isinstance(model.get("assumptions"), list):
            raise ValueError("Malformed valuation evidence")
        for row in model["assumptions"]:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise ValueError("Invalid valuation scenario identifier")
            add("valuation-scenario:" + row["id"], "valuation-scenario")
    return candidates


def validate_ai_proposal(packet, proposed):
    verified_digest = _validate_input_packet(packet)
    if not isinstance(proposed,dict):
        raise ValueError("Missing proposed review")
    expected={"version","companyId","packetContentSha256","status","analysisMode",
              "evidenceCitations","analystQuestions","interpretations",
              "suggestedScenarioReview","proposedValuationAction"}
    if set(proposed)!=expected:
        raise ValueError("Unexpected proposal keys; no mutable approvals or commands allowed")
    if proposed["version"]!=1 or proposed["companyId"]!=packet["companyId"]:
        raise ValueError("Wrong issuer or proposal version")
    if proposed["packetContentSha256"] != verified_digest:
        raise ValueError("Stale packet version; no evidence binding")
    if proposed["status"]!="requires-human-review":
        raise ValueError("AI cannot approve its own output")
    if proposed["analysisMode"] != "deterministic-no-ai":
        # There is no trusted, server-side model-execution attestation yet.
        # Accepting a model's self-declared analysisMode would let a caller
        # misrepresent deterministic output as actual AI research.
        raise ValueError("AI provenance not attested; only deterministic-no-ai is allowed")
    if proposed["proposedValuationAction"]!="no-automatic-change":
        raise ValueError("Direct financial model edits are forbidden")
    candidates=_evidence_candidates(packet)
    refs=proposed["evidenceCitations"]
    if not isinstance(refs,list) or len(refs)>100:
        raise ValueError("Unbounded citations")
    for c in refs:
        if not isinstance(c,dict) or set(c)!={"evidenceId","kind","claim","uncertainty"}:
            raise ValueError("Missing source trace for claim")
        if (not isinstance(c["evidenceId"], str) or c["evidenceId"] not in candidates
            or candidates[c["evidenceId"]]!=c["kind"]):
            raise ValueError("Fabricated or mistyped evidence reference")
        if not _str(c["claim"]) or not _str(c["uncertainty"]):
            raise ValueError("Empty claim or uncertainty")
        if c["kind"] not in KINDS:
            raise ValueError("Invalid evidence kind")
    questions=proposed["analystQuestions"]
    if not isinstance(questions,list) or len(questions)>30 or not all(_str(q) for q in questions):
        raise ValueError("Invalid analyst questions")
    interpretations=proposed["interpretations"]
    if not isinstance(interpretations,list) or len(interpretations)>40:
        raise ValueError("Invalid interpretation count")
    ids={c["evidenceId"] for c in refs}
    for item in interpretations:
        if not isinstance(item,dict) or set(item)!={"observation","hypothesis","evidenceIds","unknowns"}:
            raise ValueError("An interpretation must be cited and clearly hypothetical")
        if not _str(item["observation"]) or not _str(item["hypothesis"]):
            raise ValueError("Invalid inference text")
        if not isinstance(item["unknowns"],list) or not all(_str(v) for v in item["unknowns"]):
            raise ValueError("Missing limits")
        if not isinstance(item["evidenceIds"],list) or not item["evidenceIds"] or not all(isinstance(v,str) and v in ids for v in item["evidenceIds"]):
            raise ValueError("Interpretation references unknown or uncited source")
    scenarios=proposed["suggestedScenarioReview"]
    if not isinstance(scenarios,list) or len(scenarios)>3:
        raise ValueError("Invalid scenario review")
    if scenarios and (packet.get("valuationModel") is None or set(x.get("id") for x in scenarios if isinstance(x,dict))!=SCENARIOS):
        raise ValueError("Scenario suggestions require current quantified model and all three scenarios")
    weights=[]
    for s in scenarios:
        if not isinstance(s,dict) or set(s)!={"id","suggestedProbability","reason","evidenceIds","status"}:
            raise ValueError("Scenario review missing fields")
        if s["id"] not in SCENARIOS or not _type_is_safe(s["suggestedProbability"]) or not 0<=s["suggestedProbability"]<=100:
            raise ValueError("Invalid scenario probability")
        if s["status"]!="review-only" or not _str(s["reason"]):
            raise ValueError("Unjustified scenario or attempted promotion")
        if not isinstance(s["evidenceIds"],list) or not s["evidenceIds"] or not all(isinstance(v,str) and v in ids for v in s["evidenceIds"]):
            raise ValueError("Uncited scenario rationale")
        weights.append(s["suggestedProbability"])
    if weights and abs(sum(weights)-100)>0.001:
        raise ValueError("Scenario suggestions must total 100 percent")
    return {"valid":True,"status":"requires-human-review",
            "cited":len(refs),"interpretations":len(interpretations),
            "scenarioSuggestions":len(scenarios),"modelChanges":0}

def main():
    import argparse
    p=argparse.ArgumentParser(description="Validate externally prepared review-only AI proposal; never approve it")
    p.add_argument("--packet",required=True)
    p.add_argument("--proposal",required=True)
    args=p.parse_args()
    packet=json.loads(Path(args.packet).read_text(encoding="utf-8"))
    proposed=json.loads(Path(args.proposal).read_text(encoding="utf-8"))
    print(json.dumps(validate_ai_proposal(packet,proposed)))

if __name__=="__main__":
    main()
