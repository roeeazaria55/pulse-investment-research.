"""Fail-closed outcome/approval gate, without network or GitHub writes."""
import copy
import io
import json
import os
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest.mock import patch, Mock
import pulse_release_security as gate

SHA = 'a' * 40
HEAD = 'b' * 40
USER = {'login': gate.OWNER, 'id': gate.OWNER_ID, 'type': 'User'}
BRANCH = {'name': 'main', 'protected': True, 'commit': {'sha': SHA}, 'protection': {
    'required_status_checks': {'enforcement_level': 'everyone',
                              'checks': [{'context': 'check', 'app_id': gate.ACTIONS_APP_ID}]}}}
ENV = {'id': 10, 'name': gate.RELEASE_ENV, 'can_admins_bypass': False,
       'protection_rules': [{'type': 'required_reviewers', 'prevent_self_review': False,
                            'reviewers': [{'type': 'User', 'reviewer': USER}]}],
       'deployment_branch_policy': {'protected_branches': True, 'custom_branch_policies': False}}
PR = {'number': 64, 'merged': True, 'state': 'closed', 'draft': False,
      'merge_commit_sha': SHA, 'merged_by': USER,
      'base': {'ref': 'main', 'repo': {'full_name': gate.REPO}}, 'head': {'sha': HEAD}}
CHECK = {'id': 12, 'name': 'check', 'head_sha': HEAD, 'status': 'completed', 'conclusion': 'success',
         'app': {'id': gate.ACTIONS_APP_ID},
         'details_url': f'https://github.com/{gate.REPO}/actions/runs/25/job/45'}
CI = {'id': 25, 'path': '.github/workflows/check.yml', 'head_sha': HEAD,
      'event': 'pull_request', 'status': 'completed', 'conclusion': 'success',
      'repository': {'full_name': gate.REPO}}
RUN = {'id': 30, 'repository': {'full_name': gate.REPO}, 'head_branch': 'main',
       'head_sha': SHA, 'run_attempt': 1, 'status': 'in_progress',
       'path': '.github/workflows/research-release-proposal.yml',
       'event': 'workflow_dispatch', 'actor': USER, 'triggering_actor': USER}
APPROVAL = {'state': 'approved', 'user': USER, 'environments': [{'name': gate.RELEASE_ENV, 'id': 10}]}
CONTEXT = {'GITHUB_REPOSITORY': gate.REPO, 'GITHUB_REPOSITORY_OWNER': gate.OWNER,
           'GITHUB_REF': 'refs/heads/main', 'GITHUB_REF_PROTECTED': 'true', 'GITHUB_SHA': SHA,
           'GITHUB_RUN_ID': '30', 'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_TOKEN': 'test-only-not-a-secret',
           'RESEARCH_RELEASE_PROPOSALS_ENABLED': 'YES'}


def responses():
    return {'/branches/main': BRANCH, '/environments/' + gate.RELEASE_ENV: ENV,
            f'/commits/{SHA}/pulls?per_page=100': [PR], '/pulls/64': PR,
            f'/commits/{HEAD}/check-runs?check_name=check&filter=latest&per_page=100': {
                'total_count': 1, 'check_runs': [CHECK]},
            '/actions/runs/25': CI, '/actions/runs/30': RUN,
            '/actions/runs/30/approvals': [APPROVAL]}


class SecurityGateTests(unittest.TestCase):
    def test_verified_single_owner_can_approve_own_run_without_independent_review(self):
        with patch.dict(os.environ, CONTEXT, clear=True), patch.object(
                gate.GitHubReader, 'get', side_effect=lambda p: responses()[p]), redirect_stdout(io.StringIO()) as out:
            gate.main([])
        result = json.loads(out.getvalue())
        self.assertEqual(result['status'], 'owner-environment-approved')
        self.assertTrue(result['humanPrMergeStillRequired'])
        self.assertFalse(result['independentCodeReview'])

    def test_preflight_never_authorizes_or_fetches_approval_or_needs_enable_flag(self):
        context = {k: v for k, v in CONTEXT.items() if k not in ['RESEARCH_RELEASE_PROPOSALS_ENABLED', 'GITHUB_RUN_ID']}
        context['GITHUB_REF'] = 'refs/pull/64/merge'
        with patch.dict(os.environ, context, clear=True), patch.object(
                gate.GitHubReader, 'get', side_effect=lambda p: responses()[p]) as get, redirect_stdout(io.StringIO()) as out:
            gate.main(['--preflight'])
        result = json.loads(out.getvalue())
        self.assertFalse(result['authorized'])
        self.assertFalse(result['paidAiExecuted'])
        self.assertFalse(result['publicationExecuted'])
        self.assertFalse(any('/approvals' in c.args[0] for c in get.call_args_list))

    def test_missing_switch_context_or_token_blocks_before_network(self):
        for key, value in [('RESEARCH_RELEASE_PROPOSALS_ENABLED', 'NO'), ('GITHUB_REF', 'refs/heads/work'),
                           ('GITHUB_REPOSITORY', 'other/repo'), ('GITHUB_REF_PROTECTED', 'false'),
                           ('GITHUB_RUN_ATTEMPT', '2'), ('GITHUB_TOKEN', '')]:
            with self.subTest(key=key), patch.dict(os.environ, {**CONTEXT, key: value}, clear=True), patch.object(gate.GitHubReader, 'get') as get:
                with self.assertRaises(gate.ReleaseProtectionError): gate.main([])
                get.assert_not_called()

    def test_unprotected_or_admin_exempt_or_spoofable_ci_blocks(self):
        variants = [{}, {**BRANCH, 'protected': False}, {**BRANCH, 'name': 'pulse-data'}]
        for field, value in [('enforcement_level', 'non_admins'), ('checks', [{'context': 'check', 'app_id': None}])]:
            bad = copy.deepcopy(BRANCH); bad['protection']['required_status_checks'][field] = value; variants.append(bad)
        for bad in variants:
            with self.subTest(bad=bad), self.assertRaises(gate.ReleaseProtectionError): gate.verify_branch(bad)

    def test_environment_cannot_bypass_owner_or_lock_single_owner_out(self):
        variants = [{}, {**ENV, 'can_admins_bypass': True}, {**ENV, 'can_admins_bypass': None}]
        for key, value in [('prevent_self_review', True), ('reviewers', []),
                           ('reviewers', [{'type': 'User', 'reviewer': USER}, {'type': 'User', 'reviewer': USER}]),
                           ('reviewers', [{'type': 'Team', 'reviewer': USER}])]:
            bad = copy.deepcopy(ENV); bad['protection_rules'][0][key] = value; variants.append(bad)
        bad = copy.deepcopy(ENV); bad['deployment_branch_policy'] = None; variants.append(bad)
        for bad in variants:
            with self.subTest(bad=bad), self.assertRaises(gate.ReleaseProtectionError): gate.verify_environment(bad, gate.RELEASE_ENV)

    def test_ai_requires_exact_main_and_no_tags(self):
        env = copy.deepcopy(ENV); env.update(name=gate.AI_ENV, deployment_branch_policy={
            'protected_branches': False, 'custom_branch_policies': True})
        self.assertEqual(gate.verify_environment(env, gate.AI_ENV, [{'name': 'main', 'type': 'branch'}]), 10)
        for policies in [None, [], [{'name': '*', 'type': 'branch'}], [{'name': 'main', 'type': 'tag'}],
                         [{'name': 'main', 'type': 'branch'}, {'name': 'work', 'type': 'branch'}]]:
            with self.assertRaises(gate.ReleaseProtectionError): gate.verify_environment(env, gate.AI_ENV, policies)

    def test_main_must_be_exact_owner_merged_pr(self):
        for field, value in [('merged', False), ('draft', True), ('merge_commit_sha', HEAD), ('merged_by', {**USER, 'id': 1}),
                             ('base', {'ref': 'pulse-data', 'repo': {'full_name': gate.REPO}})]:
            with self.subTest(field=field), self.assertRaises(gate.ReleaseProtectionError):
                gate.verify_merged_pr({**PR, field: value}, SHA)

    def test_ci_cannot_reuse_old_pass_or_other_workflow(self):
        for field, value in [('conclusion', 'failure'), ('status', 'in_progress'), ('head_sha', SHA),
                             ('app', {'id': 1}), ('details_url', 'https://evil.invalid/')]:
            with self.subTest(field=field), self.assertRaises(gate.ReleaseProtectionError): gate.verify_ci([{**CHECK, field: value}], CI, HEAD)
        with self.assertRaises(gate.ReleaseProtectionError):
            gate.verify_ci([CHECK, {**CHECK, 'id': 13, 'conclusion': 'failure'}], CI, HEAD)
        for field, value in [('path', '.github/workflows/fake.yml'), ('head_sha', SHA), ('event', 'push'), ('conclusion', 'failure')]:
            with self.subTest(field=field), self.assertRaises(gate.ReleaseProtectionError): gate.verify_ci([CHECK], {**CI, field: value}, HEAD)

    def verify_approval(self, run=RUN, approvals=None):
        gate.verify_run_approval(run, approvals, run_id=30, sha=SHA, environment=gate.RELEASE_ENV, env_id=10)

    def test_no_approval_wrong_environment_identity_or_rejection_blocks(self):
        for approvals in [None, [], [{**APPROVAL, 'state': 'rejected'}], [{**APPROVAL, 'user': {**USER, 'type': 'Bot'}}],
                          [{**APPROVAL, 'environments': [{'name': gate.RELEASE_ENV, 'id': 11}]}],
                          [APPROVAL, {**APPROVAL, 'state': 'rejected'}]]:
            with self.subTest(approvals=approvals), self.assertRaises(gate.ReleaseProtectionError): self.verify_approval(approvals=approvals)

    def test_approval_cannot_replay_on_other_run_commit_attempt_actor_or_workflow(self):
        for field, value in [('id', 31), ('head_sha', HEAD), ('head_branch', 'work'), ('run_attempt', 2),
                             ('path', '.github/workflows/check.yml'), ('event', 'pull_request'),
                             ('triggering_actor', {**USER, 'login': 'other'}), ('status', 'completed')]:
            with self.subTest(field=field), self.assertRaises(gate.ReleaseProtectionError):
                self.verify_approval({**RUN, field: value}, [APPROVAL])

    def test_main_moving_during_verification_blocks(self):
        data = responses(); reads = 0
        def read(path):
            nonlocal reads
            if path == '/branches/main':
                reads += 1
                if reads > 1: return {**BRANCH, 'commit': {'sha': HEAD}}
            return data[path]
        with patch.dict(os.environ, CONTEXT, clear=True), patch.object(gate.GitHubReader, 'get', side_effect=read):
            with self.assertRaises(gate.ReleaseProtectionError): gate.main([])

    def test_api_denial_and_redirect_fail_closed_without_secret_in_error(self):
        token = 'test-token-never-print'
        opener = Mock(); opener.open.side_effect = urllib.error.HTTPError('url', 403, token, {}, None)
        with patch('urllib.request.build_opener', return_value=opener):
            with self.assertRaises(gate.ReleaseProtectionError) as error: gate.GitHubReader(token).get('/branches/main')
        self.assertNotIn(token, str(error.exception))
        with self.assertRaises(gate.ReleaseProtectionError): gate.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.invalid')

    def test_unreadable_or_incomplete_evidence_cannot_authorize(self):
        for path, bad in [('/branches/main', {}),
                          (f'/commits/{SHA}/pulls?per_page=100', []),
                          (f'/commits/{HEAD}/check-runs?check_name=check&filter=latest&per_page=100', {'total_count': 2, 'check_runs': [CHECK]}),
                          ('/actions/runs/30/approvals', [])]:
            data=responses(); data[path]=bad
            with self.subTest(path=path), patch.dict(os.environ, CONTEXT, clear=True), patch.object(gate.GitHubReader, 'get', side_effect=lambda p: data[p]):
                with self.assertRaises(gate.ReleaseProtectionError): gate.main([])

if __name__ == '__main__': unittest.main()
