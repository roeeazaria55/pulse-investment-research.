"""Regression evidence tests for automatically generated research input packets."""
import copy
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from ai_research_packets import ROOT, TICKERS, build_all, financial_observations, https_issuer_url, read_json

class AIResearchPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packets=build_all()
        cls.registry=read_json(ROOT/"public/data/official-registry.json")
        cls.dlo=next(c for c in cls.registry["companies"] if c["ticker"]=="DLO")
        cls.observations=read_json(ROOT/"public/data/auto-financial-observations.json")["observations"]

    def test_real_dlocal_issuer_packet_from_collected_facts(self):
        p=self.packets["DLO"]
        found={o["metricId"]:o["normalizedValue"] for o in p["financialObservations"]}
        self.assertEqual(found,{"revenue":399.7,"grossProfit":127.2,
                                "operatingCash":140.522,"capex":9.91})
        self.assertEqual(len(p["financialObservations"]),4)
        for o in p["financialObservations"]:
            self.assertEqual(o["reviewStatus"],"needs-reconciliation")
            self.assertEqual(o["verification"],"needs-reconciliation")
            self.assertFalse(o["modelEligible"])
            self.assertEqual(o["periodStart"],"2026-04-01")
            self.assertEqual(o["periodEnd"],"2026-06-30")
            self.assertTrue(https_issuer_url(o["sourceUrl"],self.dlo))
        self.assertTrue(p["research"]["sections"]["thesis"]["untrustedInstructions"])
        self.assertEqual(p["valuationModel"]["role"],"existing-analyst-model-not-issuer-fact")
        self.assertIsNone(p["valuationModel"]["approvedTargetPrice"])
        self.assertFalse(p["trustPolicy"]["aiAnalysisExecuted"])
        self.assertFalse(p["trustPolicy"]["includesPersonalPortfolio"])

    def test_reuses_one_contract_across_four_issuer_models(self):
        self.assertEqual(set(self.packets),set(TICKERS))
        for ticker,p in self.packets.items():
            self.assertEqual(p["ticker"],ticker)
            self.assertEqual(p["contractVersion"],1)
            self.assertEqual(len(p["contentSha256"]),64)
            self.assertIsNotNone(p["research"])
            self.assertFalse(p["trustPolicy"]["mayModifyTargetsOrProbabilities"])
        self.assertEqual(self.packets["SMCI"]["valuationModel"],None)
        self.assertIsNotNone(self.packets["IREN"]["valuationModel"])

    def test_repeated_inputs_produce_identical_packet_ids_and_content(self):
        again=build_all()
        self.assertEqual(again,self.packets)

    def test_rejects_unallowlisted_or_unsafe_issuer_urls(self):
        valid=self.observations[0]
        for url in ["http://rss.globenewswire.com/news-release/2026/08/13/test",
                    "https://evil.example/news-release/2026/08/13/test",
                    "https://rss.globenewswire.com.evil.example/news-release/2026/08/13/test",
                    "https://rss.globenewswire.com@evil.example/news-release/2026/08/13/test",
                    "https://127.0.0.1/news-release/test","javascript:alert(1)"]:
            modified={**valid,"sourceUrl":url}
            with self.assertRaises(ValueError):
                financial_observations(self.dlo,[modified],"report")

    def test_blocks_new_source_reusing_previous_approval(self):
        first=copy.deepcopy(self.observations[0])
        changed={**first,"sourceSha256":"b"*64,"reviewStatus":"pending-review",
                 "id":"observation:new-hash"}
        obs=financial_observations(self.dlo,[first,changed],"report")
        self.assertEqual(len(obs),2)
        self.assertTrue(all(not v["modelEligible"] for v in obs))
        self.assertNotEqual(obs[0]["sourceSha256"],obs[1]["sourceSha256"])

    def test_rejects_conflicting_financial_entries(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            financial_observations(self.dlo,[self.observations[0]]*2,"report")
        for field,bad in [("value",float("nan")),("value",False),
                          ("periodStart","2026-14-01"),("periodEnd","2026-01-01"),
                          ("sourceSha256","invalid"),("reviewStatus","approved")]:
            row={**self.observations[0],field:bad}
            with self.assertRaises(ValueError):
                financial_observations(self.dlo,[row],"report")

    def test_no_private_or_api_credentials_in_packet_contract(self):
        for p in self.packets.values():
            self.assertNotIn("holdings",p)
            self.assertNotIn("portfolio",p)
            self.assertNotIn("apiKey",p)
            self.assertNotIn("account",p)
            self.assertNotIn("openai",str(p).lower())
            self.assertNotIn("approve",list(p.keys()))
            self.assertNotIn("userProfile",p)

if __name__=="__main__":
    unittest.main()
