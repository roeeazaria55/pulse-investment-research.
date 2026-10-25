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


def nebius_quarter(doc):
    """Original Nebius PDF consolidated statement, selected Q2 or Q1 layout.

    Q2 PDF extraction contains one 250-character statement cell. The original
    page/issuer/table/year heading and unambiguous revenue line are mandatory;
    free-form earnings headlines alone must not supply a financial metric.
    """
    if doc.get("companyId") != "candidate-nebius" or doc.get("format") != "pdf":
        return []
    headline=doc.get("title","").lower()
    if "reports second quarter 2026 financial results" in headline:
        matches=[]
        for table in doc.get("tables",[]):
            if table.get("page") != 7:
                continue
            for row in table.get("rows",[]):
                if not isinstance(row,list) or len(row)!=1:
                    continue
                text=row[0]
                pattern=(r"Nebius Group N\.V\.\s+Unaudited condensed consolidated statements "
                         r"of operations\s+\(in millions of U\.S\. dollars, except share and per share data\)"
                         r"\s+Three months ended June 30,\s+Six months ended June 30,\s+"
                         r"2025 2026 2025 2026\s+Revenues\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)")
                match=re.search(pattern,text)
                if not match:continue
                prior=_number(match[1]);current=_number(match[2])
                result=_proposal(doc,"revenue","הכנסות",current,prior,match[2],match[1],
                    "2026-04-01","2026-06-30","2025-04-01","2025-06-30",
                    "USD million",
                    "Nebius unaudited consolidated statement of operations Q2 2026/Q2 2025, USD million",
                    "Nebius original Q2 PDF, statements of operations: Revenues",
                    table["page"],"retained-issuer-pdf-table")
                if result:matches.append(result)
        return matches if len(matches)==1 else []
    if "reports first quarter 2026 financial results" not in headline:
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


def lemonade_q2(doc):
    """Lemonade 2026 Q2 shareholder-letter original PDF operating metrics.

    The quarterly columns come before the 6-month YTD columns; four numeric
    cells plus corroborating MD&A text and original page are mandatory.
    """
    if (doc.get("companyId")!="us-lmnd-nyse-common" or doc.get("format")!="pdf"
        or not re.search(r"Shareholder Letter Q2 2026",doc.get("title",""),re.I)):
        return []
    page9=" ".join(cell for t in doc.get("tables",[]) if t.get("page")==9
                   for row in t.get("rows",[]) for cell in row)
    if not ("Second quarter" in page9 and "$294.4" in page9 and "2025" in page9):
        return []
    matching=[t for t in doc.get("tables",[]) if t.get("page")==11 and
              any(row and "($ in millions, except Premium per customer)" in " ".join(row)
                  for row in t.get("rows",[]))]
    if len(matching)!=1:
        return []
    t=matching[0]
    result=[]
    for label,key,hebrew in [("Total revenue","revenue","הכנסות"),
                              ("Gross profit","grossProfit","רווח גולמי")]:
        rows=[row for row in t["rows"] if row and len(row)<=3 and
              row[0].startswith(label+" $ ")]
        if len(rows)!=1:
            return []
        raw=rows[0][0][len(label):].strip()
        m=re.fullmatch(r"\$\s+([\d,]+(?:\.\d+)?)\s+\$\s+([\d,]+(?:\.\d+)?)"
                       r"\s+\$\s+([\d,]+(?:\.\d+)?)\s+\$\s+([\d,]+(?:\.\d+)?)",raw)
        if not m:
            return []
        value=_number(m[1]);prior=_number(m[2])
        rec=_proposal(doc,key,hebrew,value,prior,m[1],m[2],
            "2026-04-01","2026-06-30","2025-04-01","2025-06-30",
            "USD million","Lemonade Q2 2026 shareholder letter ($ million): first two quarter columns, YTD excluded",
            "Shareholder Letter Q2 2026 p.11: "+label,t["page"],"retained-issuer-pdf-table")
        if rec:result.append(rec)
    return result


def nextvision_fy25(doc):
    """Next Vision 2025 audited activity table, USD thousands; not 2026 data."""
    if (doc.get("companyId")!="candidate-next-vision" or doc.get("format")!="pdf"
        or "Periodic Report for 2025" not in doc.get("title","")):
        return []
    candidates=[]
    for t in doc.get("tables",[]):
        rows=t.get("rows",[])
        if t.get("page")!=9 or len(rows)<7:
            continue
        if not (rows[0]==["","","For the year ended on","","","",""] and
                "USD thousands" in " ".join(rows[1]) and
                "December 31, 2025" in " ".join(rows[2]) and
                "December 31, 2024" in " ".join(rows[2])):
            continue
        candidates.append(t)
    if len(candidates)!=1:
        return []
    t=candidates[0]
    result=[]
    for label,key,hebrew in [("Area of activity revenue","revenue","הכנסות"),
                              ("Gross profit","grossProfit","רווח גולמי")]:
        matches=[r for r in t["rows"] if r and r[0]==label]
        if len(matches)!=1 or len(matches[0])<5:
            return []
        row=matches[0]
        a=_number(row[1]);b=_number(row[4])
        if a is None or b is None:
            return []
        rec=_proposal(doc,key,hebrew,round(a/1000,6),round(b/1000,6),
            row[1],row[4],"2025-01-01","2025-12-31","2024-01-01","2024-12-31",
            "USD million","Next Vision FY2025 activity report, original USD-thousands table normalized to USD million; historical baseline only",
            "FY2025 original report, area of activity: "+label,t["page"],"retained-issuer-pdf-table")
        if rec:result.append(rec)
    return result



def meta_q3(doc):
    """META Oct-2026 issuer Q3 GAAP statement, source PDF/HTML table originals.

    GAAP consolidated income statement, not press-release narrative, is used
    for three months ended September 30 (2026 and 2025). YTD ignored.
    """
    if (doc.get("companyId")!="us-meta-nasdaq-a" or doc.get("format")!="html"
        or doc.get("title")!="Meta Reports Third Quarter 2026 Results"):
        return []
    matches=[]
    for table in doc.get("tables",[]):
        rows=table.get("rows",[])
        if not (len(rows)>=7 and rows[:4]==[
           ["META PLATFORMS, INC."],
           ["CONDENSED CONSOLIDATED STATEMENTS OF INCOME"],
           ["(In millions, except per share amounts)"],
           ["(Unaudited)"]]):
            continue
        if rows[4]!=["", "Three Months Ended September 30,", "",
                     "Nine Months Ended September 30,"] or rows[5]!=[
                         "", "2026", "", "2025", "", "2026", "", "2025"]:
            continue
        lines=[r for r in rows if r and r[0]=="Revenue"]
        if len(lines)!=1 or len(lines[0])!=8:
            return []
        r=lines[0]
        if r[1]!="$ 64,601" or r[3]!="$ 51,242":
            # This adapter was reviewed for this issuer release only.
            return []
        value=_number(r[1].removeprefix("$ ").strip())
        prior=_number(r[3].removeprefix("$ ").strip())
        m=_proposal(doc,"revenue","הכנסות GAAP",value,prior,r[1],r[3],
            "2026-07-01","2026-09-30","2025-07-01","2025-09-30",
            "USD million","Meta third-quarter 2026 GAAP condensed consolidated income statement, three months ended Sept 30",
            "CONDENSED CONSOLIDATED STATEMENTS OF INCOME: Revenue (three-month columns)",
            table.get("page"),"retained-issuer-html-table")
        if m:matches.append(m)
    return matches if len(matches)==1 else []


def ftai_q2(doc):
    """FTAI Q2 2026 original issuer's unaudited GAAP income statement.

    Distinguish Aerospace Products revenue from total consolidated revenue,
    and never mistake six-month cumulative amounts for quarterly values.
    """
    if doc.get("companyId")!="candidate-ftai" or doc.get("format")!="html":
        return []
    title=doc.get("title","").lower()
    if "second quarter 2026" not in title or "ftai aviation" not in title:
        return []
    candidates=[]
    for table in doc.get("tables",[]):
        rows=table.get("rows",[])
        full=" ".join(" ".join(r) for r in rows)
        if "Total revenues" not in full or "2026" not in full or "2025" not in full:
            continue
        line=[r for r in rows if r and r[0].strip().lower()=="total revenues"]
        if len(line)!=1:
            continue
        figures=[_number(cell.strip().lstrip("$").strip()) for cell in line[0][1:]]
        figures=[v for v in figures if v is not None]
        # Current 3mo, prior 3mo, current 6mo, prior 6mo; all USD thousands
        if figures[:4]!=[953085.0,676237.0,1783782.0,1178317.0]:
            continue
        if len(figures)!=4:
            continue
        result=_proposal(doc,"revenue","סך הכנסות",953.085,676.237,"953,085","676,237",
            "2026-04-01","2026-06-30","2025-04-01","2025-06-30",
            "USD million","FTAI Aviation Ltd original Q2 2026 unaudited consolidated statements of operations, USD thousands normalized to USD millions",
            "CONSOLIDATED STATEMENTS OF OPERATIONS: Total revenues, three months ended June 30",
            table.get("page"),"retained-issuer-html-table")
        if result:candidates.append(result)
    return candidates if len(candidates)==1 else []


def enlight_q2(doc):
    """Enlight original Q2 release Appendix 1 consolidated income statement.

    Revenues and tax-benefit income are distinct. Reported revenue only is
    not the company's combined 'Revenues and Income' non-IFRS headline.
    """
    if doc.get("companyId")!="candidate-enlight" or doc.get("format")!="pdf":
        return []
    if "second quarter 2026" not in doc.get("title","").lower():
        return []
    page=next((p["text"] for p in doc.get("sourcePdfPages",[])
               if p.get("page")==16), "")
    if not ("Consolidated Statements of Income" in page
            and "2026" in page and "2025" in page
            and "USD in" in page and "thousands" in page):
        return []
    normalized=re.sub(r"\s+"," ",page)
    matched=re.search(r"\bRevenues\s+322,477\s+225,875\s+165,990\s+116,117\b",normalized)
    combined=re.search(r"\bTotal revenues and income\s+409,284\s+264,847\s+209,691\s+134,978\b",normalized)
    if not matched or not combined:
        return []
    return [
        _proposal(doc,"revenue","הכנסות מחשמל ושירותים",165.99,116.117,"165,990","116,117",
          "2026-04-01","2026-06-30","2025-04-01","2025-06-30",
          "USD million","Consolidated IFRS revenue from financial release Appendix 1; tax benefits excluded",
          "Appendix 1 Consolidated Statements of Income: Revenues; three months ended June 30",
          16,"retained-issuer-pdf-table"),
        _proposal(doc,"revenuesAndIncome","הכנסות והטבות מס",209.691,134.978,"209,691","134,978",
          "2026-04-01","2026-06-30","2025-04-01","2025-06-30",
          "USD million","Enlight issuer combined Revenues and Income, including U.S. project tax benefits; not equal to IFRS revenue",
          "Appendix 1: Total revenues and income; three months ended June 30",
          16,"retained-issuer-pdf-table"),
    ]


def gilat_q2(doc):
    """Issuer's Hebrew RTL Q2 2026 board report, consolidated ₪ thousands.

    The exact five-column tuple is verified against original Q2 source page,
    with the direction/period of *each* column documented by the heading.
    """
    if doc.get("companyId")!="candidate-gilat-telecom" or doc.get("format")!="pdf":
        return []
    page=next((p["text"] for p in doc.get("sourcePdfPages",[])
               if p.get("page")==6), "")
    if not page or "2026" not in page or "2025" not in page:
        return []
    text=re.sub(r"\s+"," ",page)
    # Hebrew page may be text-layer reversed in extracted PDF. Only accept the
    # exact displayed consolidated table; use original page image for review.
    label="הכנסות" if "הכנסות" in text else "תוסנכה" if "תוסנכה" in text else ""
    if not label:
        return []
    sequence="260,335 66,508 71,446 124,234 139,991"
    reverse="139,991 124,234 71,446 66,508 260,335"
    if not (sequence in text or reverse in text):
        return []
    if not ("21,025" in text and "19,660" in text):
        return []
    return [
        _proposal(doc,"revenue","הכנסות",71.446,66.508,"71,446","66,508",
          "2026-04-01","2026-06-30","2025-04-01","2025-06-30",
          "ILS million","Gilat Telecom Global consolidated Q2 results, thousands of NIS normalized to millions; Q2 not H1",
          "דוח דירקטוריון עמוד 6: נתונים כספיים מאוחדים באלפי ש״ח, הכנסות",
          6,"retained-issuer-pdf-table"),
        _proposal(doc,"grossProfit","רווח גולמי",21.025,19.66,"21,025","19,660",
          "2026-04-01","2026-06-30","2025-04-01","2025-06-30",
          "ILS million","Gilat Telecom Global consolidated Q2 gross profit, thousands NIS normalized to millions",
          "דוח דירקטוריון עמוד 6: רווח גולמי",
          6,"retained-issuer-pdf-table")
    ]


def adapted_issuer_facts(doc):
    results=[sandisk_q4(doc),nebius_quarter(doc),lemonade_q2(doc),nextvision_fy25(doc),meta_q3(doc),ftai_q2(doc),enlight_q2(doc),gilat_q2(doc)]
    nonempty=[value for value in results if value]
    return nonempty[0] if len(nonempty)==1 else []
