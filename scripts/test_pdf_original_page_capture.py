"""PDF extraction unit tests: raw statement-page extraction, no OCR.

Synthetic readers verify the parser contract only. They do NOT establish
real issuer download availability; CI source-probe does that independently.
"""
from contextlib import contextmanager
from hashlib import sha256
from unittest.mock import patch
import json
import sys
import types
import unittest
from pathlib import Path
from report_intake import extract
from issuer_table_adapters import gilat_q2, enlight_q2

ROOT=Path(__file__).resolve().parent.parent
REGISTRY=json.loads((ROOT/"public/data/official-registry.json").read_text(encoding="utf-8"))

class Page:
    def __init__(self,n,text):
        self.page_number=n
        self.text=text
    def extract_text(self):
        return self.text
    def extract_tables(self,*a,**kw):
        return []

@contextmanager
def pdf_mock(pages):
    @contextmanager
    def opened(file):
        yield types.SimpleNamespace(pages=pages)
    with patch.dict(sys.modules,{"pdfplumber":types.SimpleNamespace(open=opened)}):
        yield

class OriginalPageCaptureTests(unittest.TestCase):
    def company(self,id):
        return next(c for c in REGISTRY["companies"] if c["id"]==id)

    def test_gilat_pdf_64_pages_raw_financial_layout(self):
        page1="GILAT TELECOM GLOBAL LTD 2026 " + "Quarterly financial statements "*8
        body="%PDF-1.7 official issuer report".encode()+b"x"*200
        page6=("תמצית הנתונים הכספיים המאוחדים המדווחים באלפי ש\"ח "
               "לתקופה של שלושה חודשים 30 ביוני 2026 2025 "
               "260,335 66,508 71,446 124,234 139,991 הכנסות "
               "181,397 46,848 50,421 88,256 97,740 עלות ההכנסות "
               "78,938 19,660 21,025 35,978 42,251 רווח גולמי ")
        with pdf_mock([Page(i,page1 if i==1 else page6 if i==6 else "supplement")
                       for i in range(1,65)]):
            out=extract(body,"application/pdf",
                "https://satcom-gilat.co.il/wp-content/uploads/2026/08/דוח-רבעון-2חצי-שנתי.pdf",
                self.company("candidate-gilat-telecom"))
        self.assertEqual(out["status"],"extracted")
        self.assertEqual(len(out["tables"]),0)
        self.assertEqual(out["sourcePdfPages"][0]["page"],6)
        self.assertEqual(out["sha256"],sha256(body).hexdigest())
        record=dict(out,companyId="candidate-gilat-telecom",id="report:"+"f"*32,
                    url="https://satcom-gilat.co.il/wp-content/uploads/2026/08/דוח-רבעון-2חצי-שנתי.pdf")
        nums={r["id"]:r for r in gilat_q2(record)}
        self.assertEqual(nums["revenue"]["value"],71.446)
        self.assertEqual(nums["revenue"]["unit"],"ILS million")

    def test_enlight_pdf_original_financial_statement_columns(self):
        body=b"%PDF-1.6"+b"0"*220
        page1="ENLIGHT RENEWABLE ENERGY REPORTS SECOND QUARTER 2026 FINANCIAL RESULTS "+ " 2026"*20
        page16=("Appendix 1 Consolidated Statements of Income "
                "For the six months ended June 30 For the three months ended June 30 "
                "2026 2025 2026 2025 USD in USD in USD in USD in thousands "
                "Revenues 322,477 225,875 165,990 116,117 "
                "Tax benefits 86,807 38,972 43,701 18,861 "
                "Total revenues and income 409,284 264,847 209,691 134,978")
        with pdf_mock([Page(i,page1 if i==1 else page16 if i==16 else "other")
                       for i in range(1,35)]):
            out=extract(body,"application/pdf",
                "https://enlightenergy.com/wp-content/uploads/2026/08/2Q26-Earnings-Release-Eng.pdf",
                self.company("candidate-enlight"))
        self.assertEqual(out["status"],"extracted")
        self.assertEqual(out["sourcePdfPages"][0]["page"],16)
        record=dict(out,companyId="candidate-enlight",id="report:"+"e"*32,
                    url="https://enlightenergy.com/wp-content/uploads/2026/08/2Q26-Earnings-Release-Eng.pdf")
        metrics={r["id"]:r for r in enlight_q2(record)}
        self.assertEqual(metrics["revenue"]["value"],165.99)
        self.assertEqual(metrics["revenuesAndIncome"]["value"],209.691)

if __name__=="__main__":
    unittest.main()
