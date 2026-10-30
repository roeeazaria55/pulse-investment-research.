import copy
import unittest
from earnings_research_candidates import build
from issuer_table_adapters import meta_q3

COMPANY_IDS=["us-meta-nasdaq-a","us-dlo-nasdaq-a"]+[f"issuer-{i}" for i in range(10)]
REGISTRY={"companies":[{"id":cid,"ticker":cid,"allowedHosts":["investor.atmeta.com" if cid=="us-meta-nasdaq-a" else "example.org"]} for cid in COMPANY_IDS]}
URL="https://investor.atmeta.com/investor-news/report"
def report(cid,sha="a"*64):
    url=URL if cid=="us-meta-nasdaq-a" else "https://example.org/report"
    return {"companyId":cid,"ticker":cid,"status":"pending-review",
            "sourceUrl":url,"sourceVersion":sha,"reportEvidence":{"url":url,"sha256":sha},
            "reportPeriod":"Q3 2026","publishedDate":"2026-10-21","contentId":"review-content-1","missing":[],
            "metrics":[{"id":"revenue","label":"הכנסות","value":64601,"previousValue":51242,
                        "periodStart":"2026-07-01","periodEnd":"2026-09-30",
                        "previousPeriodStart":"2025-07-01","previousPeriodEnd":"2025-09-30",
                        "unit":"USD million","sourceUrl":url,"reviewStatus":"pending-review",
                        "accountingBasis":"GAAP revenue"}]}
def latest():
    return {"version":1,"reports":[report(cid) for cid in COMPANY_IDS]}
def monitor():
    return [{"companyId":"us-meta-nasdaq-a","metrics":[{"id":"revenue","baseline":"Q2 2026",
              "nextCheck":"צמיחה בהכנסות","thesisRisk":"האטה"}]}]

class EarningsResearchCandidatesTests(unittest.TestCase):
    NOW="2026-10-28T20:00:00+00:00"
    def build(self,source=None,prior=None):
        return build(source or latest(),prior or {},REGISTRY,monitor(),self.NOW)
    def test_twelve_provisional_drafts_without_approval(self):
        out=self.build()
        self.assertEqual(len(out["latestByCompany"]),12)
        self.assertEqual(out["newCandidateCount"],12)
        meta=next(x for x in out["candidates"] if x["companyId"]=="us-meta-nasdaq-a")
        self.assertEqual(meta["status"],"needs-review")
        self.assertEqual(meta["publicationStatus"],"not-approved")
        self.assertEqual(meta["modelChange"],"none")
        self.assertFalse(meta["aiAnalysisExecuted"])
        self.assertEqual(meta["metrics"][0]["absoluteChange"],13359)
        self.assertEqual(meta["metrics"][0]["percentChange"],26.07)
        self.assertEqual(meta["analystReviewQuestions"][0]["thesisRisk"],"האטה")
        self.assertIsNone(meta["scenarioReview"]["base"])
    def test_rerun_is_idempotent_and_revised_digest_creates_new_candidate(self):
        first=self.build()
        second=self.build(prior=first)
        self.assertEqual(second["newCandidateCount"],0)
        self.assertEqual(len(second["candidates"]),12)
        changed=latest()
        changed["reports"][0]["sourceVersion"]="b"*64
        changed["reports"][0]["reportEvidence"]["sha256"]="b"*64
        newer=self.build(changed,second)
        self.assertEqual(newer["newCandidateCount"],1)
        self.assertEqual(len(newer["candidates"]),13)
        self.assertNotEqual(newer["latestByCompany"]["us-meta-nasdaq-a"],first["latestByCompany"]["us-meta-nasdaq-a"])
        self.assertIn(first["latestByCompany"]["us-meta-nasdaq-a"],{c["id"] for c in newer["candidates"]})
    def test_dlo_reconciliation_blocks_growth_claim(self):
        data=latest()
        dlo=data["reports"][1]
        dlo["status"]="needs-reconciliation"
        dlo["metrics"][0]["reviewStatus"]="needs-reconciliation"
        candidate=next(c for c in self.build(data)["candidates"] if c["companyId"]=="us-dlo-nasdaq-a")
        self.assertEqual(candidate["status"],"blocked")
        self.assertIsNone(candidate["metrics"][0]["previousValue"])
        self.assertIsNone(candidate["metrics"][0]["percentChange"])
    def test_incompatible_periods_fail_closed_without_hiding_current_facts(self):
        data=latest()
        data["reports"][0]["metrics"][0]["previousPeriodStart"]="2025-01-01"
        meta=next(c for c in self.build(data)["candidates"] if c["companyId"]=="us-meta-nasdaq-a")
        self.assertEqual(meta["metrics"][0]["comparisonStatus"],"blocked-incomparable-or-unreconciled")
        self.assertIsNone(meta["metrics"][0]["absoluteChange"])
    def test_rejects_spoofed_domain_and_reused_identity(self):
        data=latest()
        data["reports"][0]["sourceUrl"]="https://evil.test/report"
        with self.assertRaises(ValueError):
            self.build(data)
        data=latest()
        data["reports"][0]["reportEvidence"]["sha256"]="f"*64
        with self.assertRaises(ValueError):
            self.build(data)
        prior=self.build()
        prior["candidates"][0]["modelChange"]="automatic"
        with self.assertRaises(ValueError):
            self.build(prior=prior)
        tampered=self.build()
        tampered["candidates"][0]["metrics"][0]["value"]=1
        with self.assertRaises(ValueError):
            self.build(prior=tampered)
    def test_meta_original_gaap_q3_adapter_passes_into_versioned_candidate(self):
        doc={"companyId":"us-meta-nasdaq-a","format":"html",
             "title":"Meta Reports Third Quarter 2026 Results",
             "id":"report:"+"c"*32,"url":URL,"sha256":"a"*64,
             "tables":[{"page":None,"rows":[
                ["META PLATFORMS, INC."],["CONDENSED CONSOLIDATED STATEMENTS OF INCOME"],
                ["(In millions, except per share amounts)"],["(Unaudited)"],
                ["","Three Months Ended September 30,","","Nine Months Ended September 30,"],
                ["","2026","","2025","","2026","","2025"],
                ["Revenue","$ 64,601","", "$ 51,242","", "$ 181,712","", "$ 141,073"]]}]}
        actual=meta_q3(doc)
        self.assertEqual(len(actual),1)
        data=latest()
        data["reports"][0]["metrics"]=actual
        out=self.build(data)
        candidate=next(c for c in out["candidates"] if c["companyId"]=="us-meta-nasdaq-a")
        self.assertEqual(candidate["metrics"][0]["value"],64601)
        self.assertEqual(candidate["metrics"][0]["periodEnd"],"2026-09-30")
        self.assertEqual(candidate["metrics"][0]["previousPeriodEnd"],"2025-09-30")
        self.assertEqual(candidate["metrics"][0]["sourceSha256"],doc["sha256"])
        self.assertEqual(candidate["publicationStatus"],"not-approved")
    def test_no_invented_source_for_missing_report(self):
        data=latest()
        data["reports"][0].update({"sourceUrl":None,"sourceVersion":None,"metrics":[]})
        result=self.build(data)
        self.assertNotIn("us-meta-nasdaq-a",result["latestByCompany"])

if __name__=="__main__":unittest.main()
