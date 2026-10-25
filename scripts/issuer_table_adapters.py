"""Strict documented statement-table adapters (never text-guess financials).

These operate on preserved publisher tables. They fail closed if table layout,
period, currency, semantics or issuer identity differ from the reviewed
exemplar. A new report requires a new reviewed adapter or a stricter schema.
"""
from __future__ import annotations
import re
from datetime import date

AMOUNT = re.compile(r"^(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$")


def _number(cell):
    if not isinstance(cell, str) or not AMOUNT.fullmatch(cell.strip()):
        return None
    return float(cell.replace(",", ""))


def _proposal(doc, metric, label, value, previous, raw, raw_previous, start, end,
              start_prior, end_prior, unit, definition, row, page, scope):
    if value is None or previous is None:
        return None
    return dict(id=metric, label=label, value=value, previousValue=previous,
        changePercent=round((value-previous)/abs(previous)*100, 2) if previous else None,
        unit=unit, periodStart=start, periodEnd=end,
        previousPeriodStart=start_prior, previousPeriodEnd=end_prior,
        accountingBasis=definition, sourceRow=row,
        sourceRaw=raw, sourcePreviousRaw=raw_previous,
        sourcePage=page, sourceDocumentUrl=doc["url"] if page else None,
        sourceUrl=doc["url"], reviewStatus="pending-review",
        comparison="Same issuer table and accounting definition, historical period comparison only; not an analyst forecast surprise.",
        evidenceScope=scope, sourceSha256=doc["sha256"], reportId=doc["id"],
        sourceContext="Exact heading + currency + current/prior dates checked before extraction")


def sandisk_q4(doc):
    """Issuer's Q4 2026 financial release, explicit GAAP quarter/year comparatives."""
    if doc.get("companyId") != "candidate-sandisk" or doc.get("format") != "html":
        return []
    if "fiscal fourth quarter 2026" not in doc.get("title", "").lower():
        return []
    matches=[]
    for table in doc.get("tables", []):
        rows=table.get("rows", [])
        if len(rows)<5 or not rows[0][:4]==["", "GAAP", "", "Non-GAAP"]:
            continue
        header=rows[1]
        if not (len(header)>=10 and header[0]=="($ in millions, except per share amounts)"
                and header[1]=="Q4 2026" and header[3]=="Q4 2025"
                and header[5]=="Y/Y" and header[7]=="Q4 2026"):
            continue
        matches.append((table,rows))
    if len(matches)!=1:
        return []
    table,rows=matches[0]
    result=[]
    for label,key,hebrew in [
       ("Revenue","revenue","הכנסות"),
       ("Operating Income","operatingIncome","רווח תפעולי GAAP"),
    ]:
        found=[r for r in rows if r and r[0]==label]
        if len(found)!=1 or len(found[0])<7 or found[0][1]!="$" or found[0][5]!="$":
            continue
        row=found[0];v=_number(row[2]);prior=_number(row[6])
        metric=_proposal(doc,key,hebrew,v,prior,row[2],row[6],
          "2026-04-04","2026-07-03","2025-03-29","2025-06-27",
          "USD million","Sandisk fiscal Q4 GAAP results (13-week quarter ended July 3 2026 vs June 27 2025; prior pre-separation financials require review)",
          "Q4 FY2026 vs Q4 FY2025 GAAP: "+label,table.get("page"),"retained-issuer-html-table")
        if metric: result.append(metric)
    return result


def nebius_q1(doc):
    """Reviewed first-quarter NBIS original PDF consolidated statement, USD m."""
    if doc.get("companyId") != "candidate-nebius" or doc.get("format") != "pdf":
        return []
    if not re.search(r"reports first quarter 2026 financial results",doc.get("title",""),re.I):
        return []
    found=[]
    for table in doc.get("tables",[]):
        rows=table.get("rows",[])
        if not (isinstance(table.get("page"),int) and
                any("In USD $ millions" in " ".join(row) and "Three months ended" in " ".join(row)
                    for row in rows)):
            continue
        if not any(len(row)>=6 and row[3].startswith("2025") and row[5]=="2026" for row in rows):
            continue
        revenues=[row for row in rows if row and row[0]=="Revenues"]
        if len(revenues)!=1 or len(revenues[0])<6:
            continue
        row=revenues[0]
        value=_number(row[5]);prior=_number(row[3])
        metric=_proposal(doc,"revenue","הכנסות",value,prior,row[5],row[3],
            "2026-01-01","2026-03-31","2025-01-01","2025-03-31","USD million",
            "Nebius first-quarter unaudited consolidated statement of operations; USD million",
            "Revenues (original PDF statement of operations)",table["page"],
            "retained-issuer-pdf-table")
        if metric: found.append(metric)
    return found if len(found)==1 else []


def adapted_issuer_facts(doc):
    results=[sandisk_q4(doc),nebius_q1(doc)]
    nonempty=[value for value in results if value]
    return nonempty[0] if len(nonempty)==1 else []
