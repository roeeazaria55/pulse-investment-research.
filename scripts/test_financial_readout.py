"""Historical source-bound, zero-AI accounting margins; no speculative beats."""
import copy
import json
import unittest
from pathlib import Path

from financial_readout import source_margins
from issuer_coverage import build as build_coverage
from issuer_table_adapters import gilat_q2, lemonade_q2
from test_final_three_adapters import FinalThreeAdapterTests
from test_issuer_table_adapters import IssuerDocumentAdapterTests

ROOT=Path(__file__).resolve().parent.parent

class FinancialReadoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry=json.loads((ROOT/"public/data/official-registry.json").read_text())
        intake=json.loads((ROOT/"public/data/report-intake.json").read_text())
        cls.rows={r["companyId"]:r for r in build_coverage(registry,intake)["coverage"]}

    def test_gilat_original_page_regression_excerpt_q2_nis_percentages(self):
        m=source_margins(gilat_q2(FinalThreeAdapterTests().gilat()))
        self.assertEqual(len(m),1)
        self.assertEqual(m[0]["metricId"],"grossProfit")
        self.assertEqual(m[0]["currentMarginPercent"],round(21.025/71.446*100,2))
        self.assertEqual(m[0]["previousMarginPercent"],round(19.66/66.508*100,2))
        self.assertEqual(m[0]["unit"],"percent")
        self.assertEqual(m[0]["reviewStatus"],"pending-review")
        self.assertFalse(m[0]["modelEligible"])
        self.assertNotIn("beat",m[0]["finding"].lower())

    def test_lemonade_regression_excerpt_and_retained_smci_historical_margin(self):
        for issuer in ("us-lmnd-nyse-common","us-smci-nasdaq-common"):
            with self.subTest(issuer=issuer):
                source=(lemonade_q2(IssuerDocumentAdapterTests().lmnd()) if issuer.startswith("us-lmnd")
                        else self.rows[issuer]["typedMetrics"])
                m=source_margins(source)
                self.assertEqual(len(m),1 if issuer.startswith("us-lmnd") else 2)
                self.assertTrue(all("נקודות אחוז" in x["finding"] for x in m))
                self.assertTrue(all("מחיר יעד" in x["finding"] for x in m))
                self.assertTrue(all(x["sourceSha256"] for x in m))

    def test_wrong_currency_report_period_prior_scope_or_original_digest_rejected(self):
        original=gilat_q2(FinalThreeAdapterTests().gilat())
        for field,value in (
           ("unit","USD million"),("periodStart","2026-01-01"),
           ("previousPeriodStart","2025-01-01"),
           ("sourceSha256","a"*64),("reportId","report:"+"b"*32),
           ("reviewStatus","approved"),("sourceUrl","https://hostile.example/report")):
            with self.subTest(field=field):
                bogus=copy.deepcopy(original)
                gp=next(x for x in bogus if x["id"]=="grossProfit")
                gp[field]=value
                self.assertEqual(source_margins(bogus),[])

    def test_zero_or_missing_revenue_cannot_divide_or_claim_margin(self):
        original=gilat_q2(FinalThreeAdapterTests().gilat())
        for field,value in (("value",0),("previousValue",0),("value",float("nan"))):
            bogus=copy.deepcopy(original)
            next(x for x in bogus if x["id"]=="revenue")[field]=value
            self.assertEqual(source_margins(bogus),[])
        self.assertEqual(source_margins([]),[])
        self.assertEqual(source_margins(self.rows["candidate-ftai"]["typedMetrics"]),[])

if __name__=="__main__":
    unittest.main()
