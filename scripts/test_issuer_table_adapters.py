"""Reviewed original issuer report table cells: strict regression excerpts.

Fixture cells are transcribed verbatim from GitHub Action issuer intake artifact
40212324719, not substituted for real download or proof of archived PDF bytes.
"""
import copy
import unittest
from issuer_table_adapters import lemonade_q2, nextvision_fy25, meta_q3


class IssuerDocumentAdapterTests(unittest.TestCase):
    def lmnd(self):
        return {
            "companyId": "us-lmnd-nyse-common", "format":"pdf",
            "title":"Shareholder Letter Q2 2026 1 $1,434M $433",
            "url":"https://www.lemonade.com/investor-relations-bo/wp-content/uploads/docs/LMND-Shareholder-Letter-Q2-2026.pdf",
            "sha256":"4b42fbb6615ccf7064ff468857a03a484044b716856b2c34877722e41efe4840",
            "id":"report:"+ "a"*32,
            "tables":[
                {"page":9,"rows":[
                    ["Revenue"],
                    ["Second quarter", "revenue of", "$294.4","million increased in the second quarter of 2025"]]},
                {"page":11,"rows":[
                    ["","($ in millions, except Premium per customer)"],
                    ["Total revenue $ 294.4 $ 164.1 $ 552.4 $ 315.3",""],
                    ["Gross profit $ 113.2 $ 64.3 $ 213.3 $ 102.9",""]]}],
        }

    def nextvision(self):
        return {
            "companyId":"candidate-next-vision", "format":"pdf",
            "title":"NextVision Stabilized Systems Ltd. Periodic Report for 2025",
            "url":"https://investor-relations.nextvision-sys.com/wp-content/uploads/2025/03/Periodic_Report_2025_isa.pdf",
            "sha256":"9b03026854f0e0e3d66e1c5f03782ae73bf85eb214350a99dd7fa3966f786def",
            "id":"report:"+"b"*32,
            "tables":[{"page":9,"rows":[
                ["","","For the year ended on","","","",""],
                ["","","(USD thousands)","","","",""],
                ["","","December 31, 2025","","","December 31, 2024",""],
                ["Area of activity revenue","168,354","","","114,934","",""],
                ["Fixed costs","(8,065)","","","(4,647)","",""],
                ["Variable costs","(42,733)","","","(27,397)","",""],
                ["Gross profit","117,556","","","82,890","",""],
            ]}],
        }

    def test_lemonade_quarter_columns_not_six_month_ytd(self):
        m={x["id"]:x for x in lemonade_q2(self.lmnd())}
        self.assertEqual(set(m), {"revenue", "grossProfit"})
        self.assertEqual((m["revenue"]["value"],m["revenue"]["previousValue"]), (294.4,164.1))
        self.assertEqual((m["grossProfit"]["value"],m["grossProfit"]["previousValue"]), (113.2,64.3))
        self.assertEqual(m["revenue"]["periodEnd"],"2026-06-30")
        self.assertEqual(m["revenue"]["previousPeriodEnd"],"2025-06-30")
        self.assertEqual(m["revenue"]["sourcePage"],11)
        self.assertEqual(m["revenue"]["reviewStatus"],"pending-review")

    def test_lemonade_fail_closed_on_ambiguous_table(self):
        item=self.lmnd()
        item["tables"][1]["rows"].append(copy.deepcopy(item["tables"][1]["rows"][1]))
        self.assertEqual(lemonade_q2(item),[])
        item=self.lmnd()
        item["tables"][1]["rows"][1][0]="Revenue forecast $ 294.4 $ 164.1 $ 552.4 $ 315.3"
        self.assertEqual(lemonade_q2(item),[])

    def test_nextvision_only_2025_and_2024_usd_thousands(self):
        m={x["id"]:x for x in nextvision_fy25(self.nextvision())}
        self.assertEqual(set(m),{"revenue","grossProfit"})
        self.assertEqual((m["revenue"]["value"],m["revenue"]["previousValue"]),(168.354,114.934))
        self.assertEqual((m["grossProfit"]["value"],m["grossProfit"]["previousValue"]),(117.556,82.89))
        self.assertEqual(m["revenue"]["periodEnd"],"2025-12-31")
        self.assertEqual(m["revenue"]["sourcePage"],9)
        self.assertIn("historical baseline",m["revenue"]["accountingBasis"])

    def test_meta_q3_gaap_three_month_vs_year_to_date(self):
        doc={
            "companyId":"us-meta-nasdaq-a","format":"html",
            "title":"Meta Reports Third Quarter 2026 Results",
            "id":"report:"+"c"*32,
            "url":"https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-Third-Quarter-2026-Results/default.aspx",
            "sha256":"c180a34ae3a8e19acebcb053a48cffebb8f41a18929dc5ae94f6cb8897576a60",
            "tables":[{"page":None,"rows":[
                ["META PLATFORMS, INC."],
                ["CONDENSED CONSOLIDATED STATEMENTS OF INCOME"],
                ["(In millions, except per share amounts)"],
                ["(Unaudited)"],
                ["","Three Months Ended September 30,","","Nine Months Ended September 30,"],
                ["","2026","","2025","","2026","","2025"],
                ["Revenue","$ 64,601","", "$ 51,242","", "$ 181,712","", "$ 141,073"],
                ["Cost of revenue","13,369","","9,206","","34,917","","25,269"]
            ]}]
        }
        rows=meta_q3(doc)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["value"],64601)
        self.assertEqual(rows[0]["previousValue"],51242)
        self.assertEqual(rows[0]["periodEnd"],"2026-09-30")
        self.assertEqual(rows[0]["sourceSha256"],doc["sha256"])
        self.assertEqual(rows[0]["reviewStatus"],"pending-review")
        bad=copy.deepcopy(doc)
        bad["tables"][0]["rows"][5][1]="2025"
        self.assertEqual(meta_q3(bad),[])
        bad=copy.deepcopy(doc)
        bad["tables"][0]["rows"][6][1]="$ 74,601"
        self.assertEqual(meta_q3(bad),[])

    def test_nextvision_wrong_currency_or_years_never_used(self):
        item=self.nextvision()
        item["tables"][0]["rows"][1][2]="(NIS thousands)"
        self.assertEqual(nextvision_fy25(item),[])
        item=self.nextvision()
        item["tables"][0]["rows"][2][2]="December 31, 2026"
        self.assertEqual(nextvision_fy25(item),[])
        item=self.nextvision()
        item["tables"][0]["rows"][3][0]="Projected revenue"
        self.assertEqual(nextvision_fy25(item),[])

if __name__=="__main__":
    unittest.main()
