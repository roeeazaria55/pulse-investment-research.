"""3 issuer Q2 2026 original statement adapters: fail-closed period, currency, source tests.

These are controlled regression *excerpts*. They DO NOT substitute for an
actually retrieved PDF/HTML original and are not grounds for declaring 12/12.
"""
import copy
import unittest
from issuer_table_adapters import ftai_q2, enlight_q2, gilat_q2


class FinalThreeAdapterTests(unittest.TestCase):
    def ftai(self):
        return {
            "companyId":"candidate-ftai", "format":"html",
            "title":"FTAI Aviation Ltd. Reports Second Quarter 2026 Results",
            "sha256":"a"*64, "id":"report:"+"b"*32,
            "url":"https://ftandi.gcs-web.com/news-releases/news-release-details/ftai-aviation-ltd-reports-second-quarter-2026-results-increases",
            "tables":[{"page":None,"rows":[
                ["FTAI AVIATION LTD."],
                ["CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)"],
                ["Three Months Ended June 30,","2026","2025","Six Months Ended June 30,","2026","2025"],
                ["Aerospace products revenue","692,229","420,686","1,214,814","685,111"],
                ["Total revenues","953,085","676,237","1,783,782","1,178,317"]]}],
        }

    def enlight(self):
        return {
            "companyId":"candidate-enlight","format":"pdf",
            "title":"ENLIGHT RENEWABLE ENERGY REPORTS SECOND QUARTER 2026 FINANCIAL RESULTS",
            "url":"https://enlightenergy.com/wp-content/uploads/2026/08/2Q26-Earnings-Release-Eng.pdf",
            "sha256":"c"*64,"id":"report:"+"d"*32,
            "sourcePdfPages":[{"page":16,"text":(
                "Appendix 1 Financial information Consolidated Statements of Income "
                "For the six months ended June 30 For the three months ended June 30 "
                "2026 2025 2026 2025 USD in thousands "
                "Revenues 322,477 225,875 165,990 116,117 "
                "Tax benefits 86,807 38,972 43,701 18,861 "
                "Total revenues and income 409,284 264,847 209,691 134,978")}],
        }

    def gilat(self):
        return {
            "companyId":"candidate-gilat-telecom","format":"pdf",
            "title":"גילת טלקום גלובל בעמ דוח רבעון שני 2026",
            "url":"https://satcom-gilat.co.il/wp-content/uploads/2026/08/דוח-רבעון-2חצי-שנתי.pdf",
            "sha256":"e"*64,"id":"report:"+"f"*32,
            "sourcePdfPages":[{"page":6,"text":(
                "הנתונים הכספיים המאוחדים המדווחים באלפי ש״ח 2026 2025 "
                "260,335 66,508 71,446 124,234 139,991 הכנסות "
                "78,938 19,660 21,025 35,978 42,251 רווח גולמי")}],
        }

    def test_ftai_consolidated_quarter_revenue(self):
        figures=ftai_q2(self.ftai())
        self.assertEqual(len(figures),1)
        r=figures[0]
        self.assertEqual((r["value"],r["previousValue"]),(953.085,676.237))
        self.assertEqual(r["periodEnd"],"2026-06-30")
        self.assertEqual(r["previousPeriodEnd"],"2025-06-30")
        self.assertEqual(r["reviewStatus"],"pending-review")
        self.assertEqual(r["unit"],"USD million")
        bad=self.ftai()
        bad["tables"][0]["rows"][-1][1]="1,783,782"  # YTD mistaken as quarter
        self.assertEqual(ftai_q2(bad),[])
        bad=self.ftai()
        bad["tables"].append(copy.deepcopy(bad["tables"][0]))  # ambiguous duplicates
        self.assertEqual(ftai_q2(bad),[])

    def test_ftai_original_pdf_compatible_with_controlled_import(self):
        doc={
            "companyId":"candidate-ftai","format":"pdf",
            "title":"FTAI Aviation Ltd. Reports Second Quarter 2026 Results",
            "sha256":"a"*64,"id":"report:"+"b"*32,
            "url":"https://ftandi.gcs-web.com/node/13051/pdf",
            "sourcePdfPages":[{"page":2,"text":(
                "FTAI AVIATION LTD. CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited) "
                "Dollar amounts in thousands except share and per share data "
                "Three Months Ended June 30 Six Months Ended June 30 "
                "2026 2025 2026 2025 "
                "Aerospace products revenue 692,229 420,686 1,214,814 685,111 "
                "Total revenues 953,085 676,237 1,783,782 1,178,317")}],
        }
        r=ftai_q2(doc)
        self.assertEqual(len(r),1)
        self.assertEqual((r[0]["value"],r[0]["previousValue"]),(953.085,676.237))
        self.assertEqual(r[0]["unit"],"USD million")
        self.assertEqual(r[0]["reviewStatus"],"pending-review")
        self.assertEqual(r[0]["sourcePage"],2)
        bad=copy.deepcopy(doc)
        bad["sourcePdfPages"][0]["text"]=bad["sourcePdfPages"][0]["text"].replace("2026 2025 2026 2025","2025 2026 2025 2026")
        self.assertEqual(ftai_q2(bad),[])
        bad=copy.deepcopy(doc)
        bad["sourcePdfPages"][0]["text"]=bad["sourcePdfPages"][0]["text"].replace("953,085","953,086")
        self.assertEqual(ftai_q2(bad),[])

    def test_enlight_income_is_not_revenue(self):
        m={r["id"]:r for r in enlight_q2(self.enlight())}
        self.assertEqual(set(m),{"revenue","revenuesAndIncome"})
        self.assertEqual(m["revenue"]["value"],165.99)
        self.assertEqual(m["revenue"]["previousValue"],116.117)
        self.assertEqual(m["revenuesAndIncome"]["value"],209.691)
        self.assertEqual(m["revenuesAndIncome"]["previousValue"],134.978)
        self.assertIn("tax benefits",m["revenuesAndIncome"]["accountingBasis"])
        self.assertEqual(m["revenue"]["sourcePage"],16)
        bad=copy.deepcopy(self.enlight())
        bad["sourcePdfPages"][0]["text"]=bad["sourcePdfPages"][0]["text"].replace("2026 2025 2026 2025","2025 2026 2025 2026")
        self.assertEqual(enlight_q2(bad),[])
        bad=copy.deepcopy(self.enlight())
        bad["sourcePdfPages"][0]["text"]=bad["sourcePdfPages"][0]["text"].replace("USD in thousands","ILS in thousands")
        self.assertEqual(enlight_q2(bad),[])

    def test_gilat_shekel_quarter_vs_six_month(self):
        m={r["id"]:r for r in gilat_q2(self.gilat())}
        self.assertEqual(set(m),{"revenue","grossProfit"})
        self.assertEqual(m["revenue"]["value"],71.446)
        self.assertEqual(m["revenue"]["previousValue"],66.508)
        self.assertEqual(m["grossProfit"]["value"],21.025)
        self.assertEqual(m["grossProfit"]["previousValue"],19.66)
        self.assertEqual(m["revenue"]["unit"],"ILS million")
        self.assertIn("thousands of NIS",m["revenue"]["accountingBasis"])
        self.assertEqual(m["revenue"]["sourcePage"],6)
        bad=copy.deepcopy(self.gilat())
        bad["sourcePdfPages"][0]["text"]=bad["sourcePdfPages"][0]["text"].replace("71,446","71,447")
        self.assertEqual(gilat_q2(bad),[])
        bad=copy.deepcopy(self.gilat())
        bad["sourcePdfPages"][0]["text"]=bad["sourcePdfPages"][0]["text"].replace("2026","2024")
        self.assertEqual(gilat_q2(bad),[])


if __name__=="__main__":
    unittest.main()
