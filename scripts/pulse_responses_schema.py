"""Convert the bounded research business contract to Responses strict JSON Schema.

Business constraints (price/period/evidence/length/math) stay in local
validators; provider only guarantees structure, not investment accuracy.
Source: official OpenAI Structured Outputs guide, reviewed 2026-10-29.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
BUSINESS_SCHEMA=ROOT/"schemas/pulse-full-research-draft-v2.schema.json"

def strict_provider_schema(raw):
    """Provider-specific schema: all object keys required, no extra properties.

    Remove annotation and business validation keywords not necessary for the
    constrained decoding path. Never remove the local strict validator.
    """
    if not isinstance(raw,dict):raise ValueError("Invalid schema")
    kind=raw.get("type")
    if kind is None:
        literals=([raw["const"]] if "const" in raw else raw.get("enum"))
        if not isinstance(literals,list) or not literals:
            raise ValueError("Unsupported strict schema node")
        kinds={("boolean" if isinstance(v,bool) else "integer" if isinstance(v,int)
                else "number" if isinstance(v,float) else "string" if isinstance(v,str)
                else "null" if v is None else "invalid") for v in literals}
        if len(kinds)!=1 or "invalid" in kinds:
            raise ValueError("Unsupported mixed literal schema")
        kind=kinds.pop()
    if kind=="object":
        props=raw.get("properties")
        if not isinstance(props,dict) or raw.get("additionalProperties") is not False:
            raise ValueError("All strict response objects require closed properties")
        if set(raw.get("required",[]))!=set(props):
            raise ValueError("Strict output requires every property")
        return {"type":"object","properties":{k:strict_provider_schema(v) for k,v in props.items()},
                "required":list(props),"additionalProperties":False}
    if kind=="array":
        return {"type":"array","items":strict_provider_schema(raw["items"])}
    if kind in ("string","number","integer","boolean","null"):
        out={"type":kind}
        if "enum" in raw:out["enum"]=raw["enum"]
        if "const" in raw:out["enum"]=[raw["const"]]
        return out
    raise ValueError("Unsupported strict schema node")

def build_strict_format():
    schema=json.loads(BUSINESS_SCHEMA.read_text(encoding="utf-8"))
    # Root is object. The local financial validator retains all numeric,
    # string-length and source-citation constraints from the original contract.
    return {"type":"json_schema","name":"pulse_full_research_v2",
            "strict":True,"schema":strict_provider_schema(schema)}
