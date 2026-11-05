"""Bounded, auditable cost estimates for opt-in PULSE AI reviews.

The local ledger is NOT an OpenAI billing hard limit. Run from a serialized,
authenticated GitHub Actions workflow and set provider-side usage limits too.
No API calls are made by this module.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import re
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

def attempt_key(ticker, packet_sha, model, retry_of=None, *, rate_retry=False, generation=0):
    original = packet_key(ticker, packet_sha, model)
    if type(generation) is not int or not 0 <= generation <= 5:
        raise ValueError("Invalid reconciled attempt generation")
    if generation:
        if retry_of:
            raise ValueError("Reconciled generation cannot use owner receipt retry")
        original = hashlib.sha256((original + f"|reconciled-{generation}").encode()).hexdigest()
    if rate_retry:
        if retry_of is not None:
            raise ValueError("Rate retry is separate from owner retry")
        return hashlib.sha256((original + "|rate-retry-1").encode()).hexdigest()
    if retry_of is None:
        return original
    if retry_of != original:
        raise ValueError("Retry must reference the original receipt for this exact packet/model")
    return hashlib.sha256((original + "|owner-retry-1").encode()).hexdigest()

def validate_retry_parent(ledger, ticker, packet_sha, model, retry_of):
    attempt_key(ticker, packet_sha, model, retry_of)
    if retry_of is not None and not any(r["id"] == retry_of and "retryOf" not in r
                                      for r in ledger["calls"]):
        raise ValueError("Retry requires a settled original receipt")


def attempt_generation(ledger, ticker, packet_sha, model, retry_of=None):
    if retry_of is not None:
        return 0
    return sum(not row.get("rateRetry") and not row.get("retryOf") and
               (row["ticker"],row["packetSha256"],row["model"])==(ticker,packet_sha,model)
               for row in ledger.get("noCharge",[]))


def validate_ledger(ledger):
    if not isinstance(ledger,dict) or ledger.get("version") != 1 or not isinstance(ledger.get("calls"),list):
        raise ValueError("Cost ledger missing or malformed")
    if "holds" in ledger and not isinstance(ledger["holds"],list):
        raise ValueError("Invalid reservations")
    closed=ledger.get("noCharge",[])
    if not isinstance(closed,list):
        raise ValueError("Invalid reconciliation history")
    seen=set()
    for hold in [*ledger.get("holds",[]),*closed]:
        if (not isinstance(hold,dict) or (set(hold)-{"retryOf","rateRetry","jobId","reconciliation","generation","evidenceRef"})!={"id","ticker","model","packetSha256","heldAt","maxUsd"}
                or hold["id"]!=attempt_key(hold["ticker"],hold["packetSha256"],hold["model"],hold.get("retryOf"),rate_retry=hold.get("rateRetry",False),generation=hold.get("generation",0))
                or not Decimal(str(hold["maxUsd"])).is_finite() or Decimal(str(hold["maxUsd"]))<=0):
            raise ValueError("Invalid reserved call")
        if "jobId" in hold and not re.fullmatch(r"ai-job:[a-f0-9]{32}",str(hold["jobId"])):
            raise ValueError("Invalid reservation job identity")
        if "rateRetry" in hold and (hold["rateRetry"] is not True or "jobId" not in hold):
            raise ValueError("Invalid rate retry identity")
        month_key(hold["heldAt"])
        if hold["id"] in seen:raise ValueError("Duplicate call reservation")
        seen.add(hold["id"])
    if any(not re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}",str(h.get("evidenceRef","")))
           or "jobId" not in h for h in closed):
        raise ValueError("Closed reservation lacks a reviewed evidence reference")
    if any("evidenceRef" in h for h in ledger.get("holds",[])):
        raise ValueError("An open hold cannot carry a closure reference")
    for row in ledger["calls"]:
        if not isinstance(row,dict) or (set(row)-{"retryOf","rateRetry","jobId","generation"})!={"id","ticker","model","packetSha256","calledAt","inputTokens","outputTokens","cachedTokens","usd"}:
            raise ValueError("Ledger row malformed")
        key=attempt_key(row["ticker"], row["packetSha256"], row["model"],row.get("retryOf"),rate_retry=row.get("rateRetry",False),generation=row.get("generation",0))
        if row["id"]!=key or row["id"] in seen or month_key(row["calledAt"]) < "2026-01":
            raise ValueError("Ledger identity collision")
        seen.add(row["id"])
        raw=quoted_cost(row["model"],row["inputTokens"],row["outputTokens"],row["cachedTokens"])
        if Decimal(str(row["usd"]))!=cents(raw):
            raise ValueError("Ledger cost does not match recorded tokens")
    for item in [*ledger["calls"], *ledger.get("holds", []),*closed]:
        if "retryOf" in item:
            if not item["retryOf"]: raise ValueError("Empty retry identity")
            validate_retry_parent(ledger,item["ticker"],item["packetSha256"],item["model"],item["retryOf"])
    return ledger

def used_in_month(ledger, month: str) -> Decimal:
    validate_ledger(ledger)
    return (sum((Decimal(str(r["usd"])) for r in ledger["calls"] if month_key(r["calledAt"])==month),Decimal("0"))
            +sum((Decimal(str(h["maxUsd"])) for h in ledger.get("holds",[])),Decimal("0")))

def preflight(ledger, ticker: str, packet_sha: str, model: str, now: str,
              input_token_ceiling: int, output_token_ceiling: int=MAX_OUTPUT_TOKENS, *, retry_of=None, rate_retry=False):
    validate_ledger(ledger)
    validate_retry_parent(ledger,ticker,packet_sha,model,retry_of)
    generation=attempt_generation(ledger,ticker,packet_sha,model,retry_of)
    key=attempt_key(ticker,packet_sha,model,retry_of,rate_retry=rate_retry,generation=generation)
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
            "generation":generation,"spentUsd":str(spent),"estimatedMaxUsd":str(estimate),
            "warning":str(max((x for x in WARN_USD if spent>=x), default=Decimal("0")))}

def reserve(ledger, ticker, packet_sha, model, now, input_ceiling, output_ceiling=MAX_OUTPUT_TOKENS, *, retry_of=None, job_id=None, rate_retry=False):
    decision=preflight(ledger,ticker,packet_sha,model,now,input_ceiling,output_ceiling,retry_of=retry_of,rate_retry=rate_retry)
    if not decision["allowed"]:
        raise ValueError("Budget refused: "+decision["reason"])
    hold={"id":decision["id"],"ticker":ticker,"model":model,"packetSha256":packet_sha,
          "heldAt":now,"maxUsd":decision["estimatedMaxUsd"]}
    if retry_of is not None: hold["retryOf"]=retry_of
    if job_id is not None: hold["jobId"]=job_id
    if rate_retry: hold["rateRetry"]=True
    if decision["generation"]: hold["generation"]=decision["generation"]
    return {**ledger,"holds":[*ledger.get("holds",[]),hold]},hold

def record_call(ledger, ticker, packet_sha, model, now, usage, *, retry_of=None, rate_retry=False):
    # Record successful usage in a durable ledger; failed API calls also need
    # reconciliation against the provider before replaying the same work.
    validate_ledger(ledger)
    validate_retry_parent(ledger,ticker,packet_sha,model,retry_of)
    generation=attempt_generation(ledger,ticker,packet_sha,model,retry_of)
    key=attempt_key(ticker,packet_sha,model,retry_of,rate_retry=rate_retry,generation=generation)
    if any(r["id"]==key for r in ledger["calls"]):
        raise ValueError("Duplicate billable call identity")
    holds=ledger.get("holds",[])
    hold=next((h for h in holds if h["id"]==key),None)
    if hold is None:
        raise ValueError("No prior reserved call")
    input_tokens=usage.get("input_tokens"); output_tokens=usage.get("output_tokens")
    cached_tokens=(usage.get("input_tokens_details") or {}).get("cached_tokens",0)
    amount=cents(quoted_cost(model,input_tokens,output_tokens,cached_tokens))
    row={"id":key,"ticker":ticker,"model":model,"packetSha256":packet_sha,
         "calledAt":now,"inputTokens":input_tokens,"outputTokens":output_tokens,
         "cachedTokens":cached_tokens,"usd":str(amount)}
    for field in ("retryOf","jobId","rateRetry","generation"):
        if field in hold: row[field]=hold[field]
    return {**ledger,"calls":[*ledger["calls"],row],
            "holds":[h for h in holds if h["id"]!=key]},row
