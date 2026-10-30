"""OpenAI Responses API strict schema compatibility, with no billable call."""
import copy
import unittest
from pulse_responses_schema import build_strict_format,strict_provider_schema
from run_optional_ai_review import parse_and_validate
from ai_research_packets import build_all
from pulse_ai_pipeline import MockAIProvider

class StrictResponsesTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.packet=build_all()["DLO"]
 def test_every_object_is_closed_and_all_fields_required(self):
  fmt=build_strict_format()
  self.assertTrue(fmt["strict"])
  self.assertEqual(fmt["type"],"json_schema")
  def walk(n):
   if n["type"]=="object":
    self.assertFalse(n["additionalProperties"])
    self.assertEqual(set(n["required"]),set(n["properties"]))
    for v in n["properties"].values():walk(v)
   elif n["type"]=="array":
    walk(n["items"])
   else:
    self.assertNotIn("maxLength",n)
    self.assertNotIn("minLength",n)
    self.assertNotIn("minimum",n)
  walk(fmt["schema"])
  self.assertEqual(fmt["schema"]["properties"]["version"]["enum"],[2])
 def test_unknown_schema_nodes_are_not_silently_downgraded(self):
  with self.assertRaises(ValueError):
   strict_provider_schema({"type":"object","properties":{"x":{"type":"string"}},
                           "required":[],"additionalProperties":False})
  with self.assertRaises(ValueError):
   strict_provider_schema({"type":"object","properties":{},"required":[],
                           "additionalProperties":True})
 def test_response_refusal_and_incomplete_fail_closed(self):
  invalids=[
    {"status":"incomplete","incomplete_details":{"reason":"max_output_tokens"},"output":[]},
    {"status":"completed","incomplete_details":{"reason":"content_filter"},"output":[]},
    {"status":"completed","output":[{"type":"message","status":"completed","content":[{"type":"refusal","refusal":"no"}]}]},
    {"status":"completed","output":[{"type":"message","status":"incomplete","content":[{"type":"output_text","text":"{}"}]}]},
  ]
  for v in invalids:
   with self.subTest(v=v),self.assertRaises(ValueError):
    parse_and_validate(self.packet,v)
 def test_completed_source_bound_mock_is_not_mislabeled_as_model_result(self):
  mock=MockAIProvider().analyze(self.packet)
  response={"status":"completed","output":[{"type":"message","status":"completed",
           "content":[{"type":"output_text","text":__import__("json").dumps(mock,ensure_ascii=False)}]}]}
  with self.assertRaises(ValueError):
   parse_and_validate(self.packet,response)

if __name__=="__main__":unittest.main()
