"""Public, synthetic validator tests. These are NOT the private deployment eval."""
import copy
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import mvpctl as ctl


def profile():
    return dict(ctl.EXAMPLE, image='registry.corp.internal/opencode@sha256:' + '1' * 64,
                runtime_image='registry.corp.internal/runtime@sha256:' + '2' * 64,
                binary_sha256='3' * 64, gateway_url='https://inference.corp.internal/v1',
                model='internal-coder', model_revision='weights-2026-09-01',
                storage_class='encrypted-private', deployment_revision='integration-42',
                eval_suite_sha256='4' * 64)


def report(p):
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return {'schema_version': 1, 'decision': 'pass',
            'subject': {'profile_sha256': ctl.digest(ctl.canonical(p)), 'image': p['image'],
                        'binary_sha256': p['binary_sha256']},
            'issued_at': (now - dt.timedelta(minutes=1)).isoformat().replace('+00:00', 'Z'),
            'expires_at': (now + dt.timedelta(days=1)).isoformat().replace('+00:00', 'Z'),
            'suite_version': 'SYNTHETIC-TEST-ONLY', 'suite_sha256': p['eval_suite_sha256'],
            'evaluation_owner': 'synthetic-test-signer', 'unresolved_critical': 0,
            'unresolved_high': 0, 'waivers': [], 'gates': {
                name: {'status': 'pass', 'executed': 1, 'failed': 0, 'skipped': 0,
                       'evidence_sha256': '5' * 64} for name in ctl.GATES}}


class ProfileTests(unittest.TestCase):
    def test_valid_profile(self):
        self.assertEqual(ctl.validate_profile(profile()), profile())

    def test_unconfigured_profile_fails(self):
        with self.assertRaises(ValueError):
            ctl.validate_profile(ctl.EXAMPLE)

    def test_rejects_unsafe_or_ambiguous_configuration(self):
        changes = [('gateway_url', 'http://inference.corp.internal/v1'),
                   ('gateway_url', 'https://user:secret@inference.corp.internal/v1'),
                   ('gateway_url', 'https://inference.corp.internal/v1?x=1'),
                   ('gateway_url', 'https://inference.corp.internal/v2'),
                   ('gateway_url', 'https://inference.corp.internal:8443/v1'),
                   ('gateway_url', 'https://inference.corp.internal:443/v1'),
                   ('gateway_url', 'https://inference.example.invalid/v1'),
                   ('gateway_ipv4', '8.8.8.8'), ('gateway_ipv4', '169.254.169.254'),
                   ('gateway_ipv4', '127.0.0.1'), ('gateway_ipv4', '::1'),
                   ('image', 'registry.corp.internal/image:latest'),
                   ('image', 'registry.corp.internal/image@sha256:' + '0' * 64),
                   ('runtime_image', ''), ('binary_sha256', ''),
                   ('workspace_id', '../../escape'), ('workspace_id', 'a\nname: evil'),
                   ('model', 'REPLACE_ME'), ('model_revision', 'latest'),
                   ('deployment_revision', ''), ('storage_class', ''),
                   ('context', True), ('output', 999999), ('eval_suite_sha256', '')]
        for field, value in changes:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                ctl.validate_profile(dict(profile(), **{field: value}))

    def test_unknown_field_fails(self):
        with self.assertRaises(ValueError):
            ctl.validate_profile(dict(profile(), enable_cloud=True))

    def test_duplicate_and_nonfinite_json_fail(self):
        for raw in [b'{"image":"safe","image":"unsafe"}', b'{"x": NaN}', b'{"x": Infinity}']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                ctl.parse_json(raw)

    def test_canonical_identity_ignores_key_order(self):
        p = profile()
        self.assertEqual(ctl.digest(ctl.canonical(p)), ctl.digest(ctl.canonical(dict(reversed(list(p.items()))))))


class ReportTests(unittest.TestCase):
    def test_complete_synthetic_report(self):
        p = profile()
        self.assertEqual(ctl.check_report(p, report(p))['decision'], 'pass')

    def test_every_missing_gate_blocks(self):
        for name in ctl.GATES:
            r = report(profile()); del r['gates'][name]
            with self.subTest(gate=name), self.assertRaises(ValueError):
                ctl.check_report(profile(), r)

    def test_failed_skipped_empty_or_unproven_gate_blocks(self):
        for name in ctl.GATES:
            for field, value in [('status', 'pending'), ('executed', 0), ('executed', True),
                                 ('failed', 1), ('skipped', 1), ('evidence_sha256', '')]:
                r = report(profile()); r['gates'][name][field] = value
                with self.subTest(gate=name, field=field), self.assertRaises(ValueError):
                    ctl.check_report(profile(), r)

    def test_changed_deployment_invalidates_report(self):
        for field, value in [('model_revision', 'weights-2026-09-02'), ('gateway_ipv4', '10.77.0.11'),
                             ('workspace_id', 'other-dev'), ('deployment_revision', 'integration-43'),
                             ('image', 'registry.corp.internal/opencode@sha256:' + '9' * 64),
                             ('storage_class', 'other-storage')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                ctl.check_report(dict(profile(), **{field: value}), report(profile()))

    def test_wrong_suite_findings_waivers_and_wrong_decision_block(self):
        for field, value in [('suite_sha256', '9' * 64), ('unresolved_critical', 1),
                             ('unresolved_high', 1), ('unresolved_high', False),
                             ('waivers', ['accepted-risk']), ('decision', 'pending'), ('schema_version', True)]:
            r = report(profile()); r[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                ctl.check_report(profile(), r)

    def test_invalid_validity_windows_block(self):
        now = dt.datetime(2026, 9, 5, tzinfo=dt.timezone.utc)
        cases = [('2026-09-01T00:00:00Z', '2026-09-04T00:00:00Z'),
                 ('2026-09-06T00:00:00Z', '2026-09-07T00:00:00Z'),
                 ('2026-09-01T00:00:00Z', '2026-10-10T00:00:00Z'),
                 ('2026-09-01T00:00:00', '2026-09-07T00:00:00Z')]
        for start, end in cases:
            r = report(profile()); r.update(issued_at=start, expires_at=end)
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                ctl.check_report(profile(), r, now)


class DeploymentTests(unittest.TestCase):
    def test_manifests_constrain_identity_network_storage_and_process(self):
        objects = ctl.manifests(profile(), 'evaluation')
        namespace, network, work, state, pod = objects
        self.assertEqual(namespace['metadata']['labels']['pod-security.kubernetes.io/enforce'], 'restricted')
        self.assertEqual(network['spec']['podSelector'], {})
        self.assertEqual(network['spec']['ingress'], [])
        self.assertEqual(network['spec']['egress'], [{'to': [{'ipBlock': {'cidr': '10.77.0.10/32'}}],
                                                     'ports': [{'protocol': 'TCP', 'port': 443}]}])
        self.assertNotEqual(work['metadata']['name'], state['metadata']['name'])
        spec = pod['spec']; container = spec['containers'][0]
        self.assertFalse(spec['automountServiceAccountToken'])
        self.assertFalse(spec['hostNetwork'])
        self.assertEqual(spec['dnsPolicy'], 'None')
        self.assertEqual(spec['securityContext']['runAsUser'], 10001)
        self.assertTrue(container['securityContext']['readOnlyRootFilesystem'])
        self.assertFalse(container['securityContext']['allowPrivilegeEscalation'])
        self.assertEqual(container['securityContext']['capabilities']['drop'], ['ALL'])
        self.assertEqual(container['image'], profile()['image'])
        self.assertEqual(pod['metadata']['labels']['opencode.stage'], 'evaluation')

    def test_accepted_manifest_requires_proof_identity(self):
        with self.assertRaises(ValueError):
            ctl.manifests(profile(), 'accepted')

    def test_image_context_checks_binary_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp); binary = tmp / 'binary'; binary.write_bytes(b'synthetic-binary')
            p = dict(profile(), image='', binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
            output = tmp / 'context'; ctl.image_context(p, binary, output)
            self.assertEqual((output / 'opencode').read_bytes(), binary.read_bytes())
            self.assertEqual(json.loads((output / 'enterprise.json').read_text()), ctl.policy(p))
            dockerfile = (output / 'Dockerfile').read_text()
            self.assertIn('FROM ' + p['runtime_image'], dockerfile)
            self.assertIn('USER 10001:10001', dockerfile)
            with self.assertRaises(FileExistsError):
                ctl.image_context(p, binary, output)

    def test_bad_binary_does_not_create_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp); binary = tmp / 'binary'; binary.write_bytes(b'wrong')
            with self.assertRaises(ValueError):
                ctl.image_context(profile(), binary, tmp / 'context')
            self.assertFalse((tmp / 'context').exists())

    def test_cli_blocks_accepted_render_without_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp); p = tmp / 'profile.json'; p.write_text(json.dumps(profile()))
            result = subprocess.run([sys.executable, str(pathlib.Path(ctl.__file__)), 'render', '--stage', 'accepted',
                                     '--profile', str(p), '--output', str(tmp / 'accepted')], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((tmp / 'accepted').exists())


class SignatureTests(unittest.TestCase):
    def test_real_ed25519_signature_tampering_and_wrong_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            for name in ('approved', 'untrusted'):
                subprocess.run(['openssl', 'genpkey', '-algorithm', 'ED25519', '-out', str(tmp / (name + '.key'))],
                               check=True, capture_output=True)
                subprocess.run(['openssl', 'pkey', '-in', str(tmp / (name + '.key')), '-pubout',
                                '-out', str(tmp / (name + '.pub'))], check=True, capture_output=True)
            payload = tmp / 'report.json'; payload.write_bytes(ctl.canonical(report(profile())))
            sig = tmp / 'report.sig'
            subprocess.run(['openssl', 'pkeyutl', '-sign', '-inkey', str(tmp / 'approved.key'), '-rawin',
                            '-in', str(payload), '-out', str(sig)], check=True, capture_output=True)
            self.assertEqual(ctl.verify_report(profile(), payload, sig, tmp / 'approved.pub')['decision'], 'pass')
            config = tmp / 'profile.json'; config.write_bytes(ctl.canonical(profile()))
            accepted = tmp / 'accepted'
            cli = subprocess.run([sys.executable, str(pathlib.Path(ctl.__file__)), 'render', '--stage', 'accepted',
                                  '--profile', str(config), '--report', str(payload), '--signature', str(sig),
                                  '--trusted-key', str(tmp / 'approved.pub'), '--output', str(accepted)], capture_output=True)
            self.assertEqual(cli.returncode, 0, cli.stderr)
            pod = json.loads((accepted / '02-workspace.json').read_text())
            self.assertEqual(pod['metadata']['labels']['opencode.stage'], 'accepted')
            self.assertEqual(pod['metadata']['annotations']['opencode.eval-sha256'],
                             ctl.digest(ctl.canonical(json.loads(payload.read_bytes()))))
            with self.assertRaises(ValueError):
                ctl.verify_report(profile(), payload, sig, tmp / 'untrusted.pub')
            payload.write_bytes(payload.read_bytes() + b' ')
            with self.assertRaises(ValueError):
                ctl.verify_report(profile(), payload, sig, tmp / 'approved.pub')
            sig.write_bytes(b'short')
            with self.assertRaises(ValueError):
                ctl.verify_report(profile(), payload, sig, tmp / 'approved.pub')

    def test_pending_public_template_cannot_authorize_deployment(self):
        template = pathlib.Path(ctl.__file__).resolve().parents[1] / 'assurance/report.example.json'
        with self.assertRaises(ValueError):
            ctl.check_report(profile(), ctl.read_json(template))

    def test_oversized_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'oversized'; path.write_bytes(b'a' * 65)
            with self.assertRaises(ValueError):
                ctl.read_limited(path, 64)


if __name__ == '__main__':
    unittest.main()
