"""SEC XBRL CompanyFacts Q2 2026 fallback: issuer source and period guards.

Only synthetic SEC-JSON *fixtures*. The PR's actual CI source probe alone
establishes whether SEC allowed real, non-authenticated HTTP retrieval.
"""
import copy
import hashlib
import json
import unittest
from datetime import date

from ftai_sec_companyfacts import SEC_URL, Q2_ACCESSION, read_ftai_companyfacts
from report_intake import extract
from issuer_coverage import safe_source_facts, build
from latest_research_updates import other_issuer_update
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent


class FTAISecJSONTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r=json.loads((ROOT/"public/data/official-registry.json").read_text())
        cls.company=next(c for c in r["companies"] if c["id"]=="candidate-ftai")

    def sample(self):
        def facts(x,y,tag):
            return {"label":tag, "units":{"USD":[
                {"start":"2026-04-01","end":"2026-06-30","accn":Q2_ACCESSION,
                 "form":"10-Q","filed":"2026-07-31","fy":2026,"fp":"Q2","val":x},
                {"start":"2025-04-01","end":"2025-06-30","accn":Q2_ACCESSION,
                 "form":"10-Q","filed":"2026-07-31","fy":2026,"fp":"Q2","val":y},
                # A larger year-to-date total must NOT replace Q2.
                {"start":"2026-01-01","end":"2026-06-30","accn":Q2_ACCESSION,
                 "form":"10-Q","filed":"2026-07-31","val":x*2},
            ]}}
        return {
            "cik":1590364,"entityName":"FTAI AVIATION LTD.",
            "facts":{"us-gaap":{
                "Revenues":facts(953085000,676237000,"Revenues"),
                "OperatingIncomeLoss":facts(166040000,177090000,"OperatingIncomeLoss"),
                "NetIncomeLoss":facts(125094000,165398000,"NetIncomeLoss"),
                "NetCashProvidedByUsedInOperatingActivities":
                  {"units":{"USD":[{"start":"2026-01-01","end":"2026-06-30",
                   "accn":Q2_ACCESSION,"form":"10-Q","filed":"2026-07-31","val":100000000}]}}
            }}
        }

    def parsed(self, doc):
        raw=json.dumps(doc,sort_keys=True).encode()
        result=extract(raw,"application/json",SEC_URL,self.company)
        self.assertEqual(result["sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["format"],"sec-json")
        self.assertEqual(result["secAccession"],Q2_ACCESSION)
        self.assertTrue(all(f["context"].endswith(Q2_ACCESSION) for f in result["facts"]))
        return result

    def test_sec_json_prevents_q2_ytd_confusion_and_ingests_exact_historical_quarter(self):
        result=self.parsed(self.sample())
        self.assertEqual(len(result["facts"]),6)
        self.assertFalse(any(f["start"]=="2026-01-01" for f in result["facts"]))
        report=dict(result,id="report:"+"a"*32,companyId=self.company["id"],
                    url=SEC_URL,publishedDate="2026-07-31",
                    documentPeriod="Q2 2026",firstDetectedAt="2026-10-26T00:00:00Z",
                    lastSuccessfulAt="2026-10-26T00:00:00Z")
        coverage=build({"companies":[self.company]+[
            c for c in json.loads((ROOT/"public/data/official-registry.json").read_text())["companies"]
            if c["id"]!=self.company["id"]]},
            {"documents":[report],"sources":[{"companyId":self.company["id"],"status":"ok"}]})
        row=coverage["coverage"][0]
        self.assertEqual(row["metricCoverage"],"provisional-structured")
        metrics={m["id"]:m for m in row["typedMetrics"]}
        self.assertEqual(set(metrics),{"revenue","operatingIncome","netIncome"})
        self.assertEqual((metrics["revenue"]["value"],metrics["revenue"]["previousValue"]),
                         (953.085,676.237))
        self.assertEqual(metrics["revenue"]["periodStart"],"2026-04-01")
        self.assertEqual(metrics["revenue"]["previousPeriodStart"],"2025-04-01")
        self.assertEqual(metrics["revenue"]["evidenceScope"],"retained-sec-companyfacts-xbrl")
        self.assertEqual(metrics["revenue"]["sourceSha256"],result["sha256"])
        rendered=other_issuer_update(row)
        self.assertEqual(rendered["status"],"pending-review")
        self.assertEqual(rendered["sourceDigestKind"],"retained-sec-companyfacts-json-sha256")
        self.assertEqual(rendered["aiAnalysisEnabled"],False)
        self.assertEqual(rendered["reviewRequired"],True)

    def test_reject_wrong_company_identity_publication_or_accession(self):
        for field,value in [("cik",1590365),("entityName","GILAT SATELLITE NETWORKS"),
                            ("entityName","FTAI Aviation competitor")]:
            with self.subTest(field=field):
                x=self.sample();x[field]=value
                with self.assertRaisesRegex(ValueError,"issuer CIK/name"):
                    self.parsed(x)
        x=self.sample()
        for fact in x["facts"]["us-gaap"]["Revenues"]["units"]["USD"]:
            fact["accn"]="0001628280-26-050622"
        # Other metrics still valid, but revenue must never be invented.
        extracted=self.parsed(x)["facts"]
        self.assertFalse(any(f["concept"]=="us-gaap:revenues" for f in extracted))

    def test_reject_ambiguous_same_period_and_wrong_period_data(self):
        x=self.sample()
        r=x["facts"]["us-gaap"]["Revenues"]["units"]["USD"][0]
        other={**r,"val":r["val"]+1}
        x["facts"]["us-gaap"]["Revenues"]["units"]["USD"].append(other)
        self.assertNotIn("us-gaap:revenues",{f["concept"] for f in self.parsed(x)["facts"]})
        x=self.sample()
        x["facts"]["us-gaap"]["Revenues"]["units"]["USD"][0]["start"]="2026-01-01"
        self.assertNotIn("us-gaap:revenues",{f["concept"] for f in self.parsed(x)["facts"]})

    def test_reject_json_with_bad_media_wrong_url_and_no_qualifying_facts(self):
        x=self.sample();raw=json.dumps(x).encode()
        with self.assertRaises(ValueError):
            extract(raw,"application/json",SEC_URL,{**self.company,"id":"candidate-nebius"})
        with self.assertRaisesRegex(ValueError,"requires JSON"):
            extract(raw,"text/html",SEC_URL,self.company)
        with self.assertRaisesRegex(ValueError,"No uniquely comparable"):
            read_ftai_companyfacts(json.dumps({"cik":1590364,"entityName":"FTAI AVIATION LTD.",
                                               "facts":{"us-gaap":{}}}).encode(),SEC_URL,self.company)


if __name__=="__main__":
    unittest.main()
