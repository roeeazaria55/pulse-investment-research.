"""Bounded, auditable cost estimates for opt-in PULSE AI reviews.

The local ledger is NOT an OpenAI billing hard limit. Run from a serialized,
authenticated GitHub Actions workflow and set provider-side usage limits too.
No API calls are made by this module.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from decimal import Decimal, ROUND_UP, ROUND_HALF_UP

BUDGET_USD = Decimal("10.00")
START_BLOCK_USD = Decimal("9.00")
WARN_USD = (Decimal("5.00"), Decimal("8.00"))
MAX_CALL_USD = Decimal("1.00")
MAX_OUTPUT_TOKENS = 3000
# Verified OpenAI Standard prices (USD/million tokens) on 2026-10-29.
# Review prices before activation; overrides are not accepted from untrusted data.
MODEL_RATES = {
    "gpt-6-luna": (Decimal("0.10"), Decimal("0.50"), Decimal("0.01")),
    "gpt-6.1-sol": (Decimal("2.00"), Decimal("10.00"), Decimal("0.10")),
}

def month_key(now: str) -> str:
    timestamp = dt.datetime.fromisoformat(now.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("UTC timestamp required")
    return timestamp.astimezone(dt.timezone.utc).strftime("%Y-%m")

def cents(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_UP)

def quoted_cost(model: str, input_tokens: int, output_tokens: int, cached_tokens: int=0) -> Decimal:
    if model not in MODEL_RATES:
        raise ValueError("Model not approved for bounded budget")
    if (not all(type(v) is int and v >= 0 for v in (input_tokens, output_tokens, cached_tokens))
            or cached_tokens > input_tokens):
        raise ValueError("Invalid token accounting")
    inp, out, cached = MODEL_RATES[model]
    return ((Decimal(input_tokens-cached)*inp + Decimal(cached_tokens)*cached
             + Decimal(output_tokens)*out) / Decimal(1_000_000))

def packet_key(ticker: str, packet_sha: str, model: str) -> str:
    if not (isinstance(ticker,str) and ticker.strip() and isinstance(packet_sha,str)
            and len(packet_sha)==64 and set(packet_sha)<=set("0123456789abcdef")
            and model in MODEL_RATES):
        raise ValueError("Invalid packet identity")
    return hashlib.sha256((ticker+"|"+packet_sha+"|"+model).encode()).hexdigest()

def validate_ledger(ledger):
    if not isinstance(ledger,dict) or ledger.get("version") != 1 or not isinstance(ledger.get("calls"),list):
        raise ValueError("Cost ledger missing or malformed")
    if "holds" in ledger and not isinstance(ledger["holds"],list):
        raise ValueError("Invalid reservations")
    seen=set()
    for hold in ledger.get("holds",[]):
        if (not isinstance(hold,dict) or set(hold)!={"id","ticker","model","packetSha256","heldAt","maxUsd"}
                or hold["id"]!=packet_key(hold["ticker"],hold["packetSha256"],hold["model"])
                or Decimal(str(hold["maxUsd"]))<=0):
            raise ValueError("Invalid reserved call")
        month_key(hold["heldAt"])
        if hold["id"] in seen:raise ValueError("Duplicate call reservation")
        seen.add(hold["id"])
    for row in ledger["calls"]:
        if not isinstance(row,dict) or set(row)!={"id","ticker","model","packetSha256","calledAt","inputTokens","outputTokens","cachedTokens","usd"}:
            raise ValueError("Ledger row malformed")
        key=packet_key(row["ticker"], row["packetSha256"], row["model"])
        if row["id"]!=key or row["id"] in seen or month_key(row["calledAt"]) < "2026-01":
            raise ValueError("Ledger identity collision")
        seen.add(row["id"])
        raw=quoted_cost(row["model"],row["inputTokens"],row["outputTokens"],row["cachedTokens"])
        if Decimal(str(row["usd"]))!=cents(raw):
            raise ValueError("Ledger cost does not match recorded tokens")
    return ledger

def used_in_month(ledger, month: str) -> Decimal:
    validate_ledger(ledger)
    return (sum((Decimal(str(r["usd"])) for r in ledger["calls"] if month_key(r["calledAt"])==month),Decimal("0"))
            +sum((Decimal(str(h["maxUsd"])) for h in ledger.get("holds",[]) if month_key(h["heldAt"])==month),Decimal("0")))

def preflight(ledger, ticker: str, packet_sha: str, model: str, now: str,
              input_token_ceiling: int, output_token_ceiling: int=MAX_OUTPUT_TOKENS):
    validate_ledger(ledger)
    key=packet_key(ticker,packet_sha,model)
    if any(r["id"]==key for r in ledger["calls"]) or any(h["id"]==key for h in ledger.get("holds",[])):
        return {"allowed":False,"reason":"already-processed-or-reserved","estimatedMaxUsd":None}
    month=month_key(now)
    spent=used_in_month(ledger,month)
    estimate=cents(quoted_cost(model,input_token_ceiling,output_token_ceiling))
    if estimate>MAX_CALL_USD:
        return {"allowed":False,"reason":"per-call-limit","estimatedMaxUsd":str(estimate)}
    if spent>=START_BLOCK_USD or spent+estimate>START_BLOCK_USD:
        return {"allowed":False,"reason":"monthly-reserve","estimatedMaxUsd":str(estimate)}
    return {"allowed":True,"reason":"approved-budget-window","id":key,"month":month,
            "spentUsd":str(spent),"estimatedMaxUsd":str(estimate),
            "warning":str(max((x for x in WARN_USD if spent>=x), default=Decimal("0")))}

def reserve(ledger, ticker, packet_sha, model, now, input_ceiling, output_ceiling=MAX_OUTPUT_TOKENS):
    decision=preflight(ledger,ticker,packet_sha,model,now,input_ceiling,output_ceiling)
    if not decision["allowed"]:
        raise ValueError("Budget refused: "+decision["reason"])
    hold={"id":decision["id"],"ticker":ticker,"model":model,"packetSha256":packet_sha,
          "heldAt":now,"maxUsd":decision["estimatedMaxUsd"]}
    return {"version":1,"calls":ledger["calls"],"holds":[*ledger.get("holds",[]),hold]},hold

def record_call(ledger, ticker, packet_sha, model, now, usage):
    # Record successful usage in a durable ledger; failed API calls also need
    # reconciliation against the provider before any further spending.
    validate_ledger(ledger)
    key=packet_key(ticker,packet_sha,model)
    if any(r["id"]==key for r in ledger["calls"]):
        raise ValueError("Duplicate billable call identity")
    holds=ledger.get("holds",[])
    if not any(h["id"]==key for h in holds):
        raise ValueError("No prior reserved call")
    input_tokens=usage.get("input_tokens"); output_tokens=usage.get("output_tokens")
    cached_tokens=(usage.get("input_tokens_details") or {}).get("cached_tokens",0)
    amount=cents(quoted_cost(model,input_tokens,output_tokens,cached_tokens))
    row={"id":key,"ticker":ticker,"model":model,"packetSha256":packet_sha,
         "calledAt":now,"inputTokens":input_tokens,"outputTokens":output_tokens,
         "cachedTokens":cached_tokens,"usd":str(amount)}
    return {"version":1,"calls":[*ledger["calls"],row],
            "holds":[h for h in holds if h["id"]!=key]},row
