import unittest
from financial_integrity_audit import audit

REGISTRY={"companies":[{"id":"us-dlo-nasdaq-a","allowedHosts":["ir.dlocal.com"]},
                        {"id":"candidate-iren","allowedHosts":["iren.gcs-web.com"]}]}
def report(company,metrics=None,status="pending-review"):
    url="https://ir.dlocal.com/results" if company=="us-dlo-nasdaq-a" else "https://iren.gcs-web.com/results"
    return {"companyId":company,"ticker":company,"status":status,"sourceUrl":url,
            "sourceVersion":"a"*64,"reportPeriod":"Q2 2026","publishedDate":"2026-08-01",
            "metrics":metrics or []}

class FinancialIntegrityAuditTests(unittest.TestCase):
    def test_unapproved_rows_remain_visible_as_pending(self):
        result=audit({"reports":[report("us-dlo-nasdaq-a"),report("candidate-iren")]},REGISTRY)
        self.assertTrue(result["safe"])
        self.assertEqual(result["companyCount"],2)
        self.assertEqual(result["metricCount"],0)
        self.assertFalse(any(x["analystApproved"] for x in result["companies"]))

    def test_wrong_source_and_invalid_period_fail_closed(self):
        metric={"id":"revenue","value":100,"periodStart":"2026-07-01","periodEnd":"2026-06-30",
                "sourceUrl":"https://evil.example","reviewStatus":"pending-review","previousValue":None}
        result=audit({"reports":[report("us-dlo-nasdaq-a",[metric]),report("candidate-iren")]},REGISTRY)
        self.assertFalse(result["safe"])
        self.assertTrue(any("source differs" in e for e in result["errors"]))
        self.assertTrue(any("accounting period" in e for e in result["errors"]))

    def test_dlo_comparison_is_blocked(self):
        metric={"id":"tpv","value":110,"periodStart":"2026-04-01","periodEnd":"2026-06-30",
                "sourceUrl":"https://ir.dlocal.com/results","reviewStatus":"pending-review",
                "previousValue":100,"previousPeriodStart":"2025-04-01","previousPeriodEnd":"2025-06-30",
                "changePercent":10}
        out=audit({"reports":[report("us-dlo-nasdaq-a",[metric]),report("candidate-iren")]},REGISTRY)
        self.assertFalse(out["safe"])
        self.assertIn("DLO: unreconciled historical comparison",out["errors"])

    def test_missing_and_duplicate_company_fail(self):
        out=audit({"reports":[report("candidate-iren"),report("candidate-iren")]},REGISTRY)
        self.assertFalse(out["safe"])
        self.assertTrue(any("missing company" in e for e in out["errors"]))
        self.assertTrue(any("duplicate company" in e for e in out["errors"]))
if __name__=="__main__": unittest.main()
