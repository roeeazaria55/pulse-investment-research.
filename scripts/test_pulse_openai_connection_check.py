import copy
import io
import json
import os
from pathlib import Path
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest.mock import Mock, patch
import pulse_openai_connection_check as probe
import pulse_release_security as gate
from test_pulse_release_security import RUN, APPROVAL, SHA, CONTEXT


class ConnectionTests(unittest.TestCase):
    def run_probe(self, body=None, error=None, context=None):
        response = Mock(status=200)
        response.read.return_value = json.dumps(body or {"id": probe.MODEL, "object": "model"}).encode()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = response
        opener.open.side_effect = error
        output = io.StringIO()
        env = {"OPENAI_API_KEY": "test-private-value", "PAID_AI_ENABLED": "NO"}
        env.update(context or {})
        with patch.dict(os.environ, env, clear=True), patch.object(probe.urllib.request, 'build_opener', return_value=opener), redirect_stdout(output):
            code = probe.main()
        self.assertNotIn('test-private-value', output.getvalue())
        return code, json.loads(output.getvalue()), opener

    def test_only_fixed_get_no_request_body_and_no_generation(self):
        code, result, opener = self.run_probe()
        self.assertEqual(code, 0)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, probe.URL)
        self.assertEqual(request.get_method(), 'GET')
        self.assertIsNone(request.data)
        self.assertEqual(opener.open.call_count, 1)
        self.assertFalse(result['generationExecuted'])
        self.assertFalse(result['billingVerified'])
        self.assertFalse(result['responsesPermissionVerified'])

    def test_missing_secret_or_paid_switch_blocks_before_network(self):
        for env in ({'OPENAI_API_KEY': ''}, {'OPENAI_API_KEY': 'bad\nkey'}, {'PAID_AI_ENABLED': 'YES'}, {'PAID_AI_ENABLED': ''}):
            code, _, opener = self.run_probe(context=env)
            self.assertEqual(code, 1)
            opener.open.assert_not_called()

    def test_failures_are_redacted_and_never_retried(self):
        for status, reason in [(401,'authentication-rejected'), (403,'permission-denied'), (404,'model-unavailable-or-not-permitted'), (429,'rate-or-quota-limited'), (500,'provider-http-error')]:
            error = urllib.error.HTTPError(probe.URL, status, 'test-private-value', {}, io.BytesIO(b'test-private-value'))
            code, result, opener = self.run_probe(error=error)
            self.assertEqual((code, result['reason']), (1, reason))
            self.assertEqual(opener.open.call_count, 1)
        for error in [urllib.error.URLError('test-private-value'), TimeoutError('test-private-value')]:
            self.assertEqual(self.run_probe(error=error)[0], 1)

    def test_wrong_model_or_invalid_body_fails(self):
        self.assertEqual(self.run_probe(body={'id':'other','object':'model'})[0], 1)
        with self.assertRaises(probe.CheckError):
            probe.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.example')

    def test_connection_approval_cannot_authorize_paid_workflow(self):
        run = copy.deepcopy(RUN)
        run['path'] = '.github/workflows/openai-connection-check.yml'
        approval = copy.deepcopy(APPROVAL)
        approval['environments'][0]['name'] = gate.AI_ENV
        kwargs = dict(run_id=30, sha=SHA, environment=gate.AI_ENV, env_id=10)
        gate.verify_run_approval(run, [approval], connection_check=True, **kwargs)
        with self.assertRaises(gate.ReleaseProtectionError):
            gate.verify_run_approval(run, [approval], **kwargs)
        with self.assertRaises(gate.ReleaseProtectionError):
            gate.verify_run_approval(run, [], connection_check=True, **kwargs)
        run['event'] = 'schedule'
        with self.assertRaises(gate.ReleaseProtectionError):
            gate.verify_run_approval(run, [approval], connection_check=True, **kwargs)

    def test_connection_gate_checks_current_run_and_emits_no_paid_authority(self):
        run = {**RUN, 'path': '.github/workflows/openai-connection-check.yml'}
        approval = copy.deepcopy(APPROVAL)
        approval['environments'][0]['name'] = gate.AI_ENV
        from test_pulse_release_security import BRANCH
        api = Mock()
        api.get.side_effect = [run, [approval], BRANCH]
        evidence = {'mainSha': SHA, 'environmentId': 10}
        output = io.StringIO()
        with patch.dict(os.environ, {**CONTEXT, 'PAID_AI_ENABLED':'NO'}, clear=True), patch.object(gate, 'GitHubReader', return_value=api), patch.object(gate, 'collect_evidence', return_value=evidence), redirect_stdout(output):
            gate.main(['--environment', gate.AI_ENV, '--connection-check'])
        result = json.loads(output.getvalue())
        self.assertFalse(result['paidAiAuthorized'])
        self.assertFalse(result['publicationAuthorized'])
        self.assertEqual(api.get.call_count, 3)

    def test_gate_requires_explicit_NO_before_reading_github(self):
        for switch in ('YES', ''):
            with patch.dict(os.environ, {**CONTEXT, 'PAID_AI_ENABLED':switch}, clear=True), patch.object(gate, 'GitHubReader') as reader:
                with self.assertRaises(gate.ReleaseProtectionError):
                    gate.main(['--environment', gate.AI_ENV, '--connection-check'])
                reader.assert_not_called()

    def test_workflow_is_manual_read_only_and_secret_is_after_approval(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/openai-connection-check.yml').read_text()
        self.assertIn('workflow_dispatch:', workflow)
        self.assertNotIn('schedule:', workflow)
        self.assertNotIn(': write', workflow)
        self.assertNotIn('upload-artifact', workflow)
        self.assertIn('environment: pulse-ai-paid', workflow)
        self.assertIn("vars.PAID_AI_ENABLED == 'NO'", workflow)
        self.assertLess(workflow.index('--connection-check'), workflow.index('OPENAI_API_KEY:'))
        ai = (root / '.github/workflows/ai-automation.yml').read_text()
        self.assertIn("github.event_name == 'schedule' && vars.PAID_AI_SCHEDULE_ENABLED == 'YES'", ai)


if __name__ == '__main__':
    unittest.main()
