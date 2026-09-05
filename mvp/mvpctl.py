#!/usr/bin/env python3
"""Offline MVP configuration and acceptance tooling. Never executes private eval cases."""
import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import pathlib
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

GATES = (
    'model_isolation', 'egress_isolation', 'workspace_isolation', 'secret_isolation',
    'policy_integrity', 'tool_permissions', 'prompt_injection', 'identity_revocation',
    'audit_retention', 'restore_rollback', 'supply_chain', 'model_functionality',
    'reliability',
)
FIELDS = {
    'schema_version', 'workspace_id', 'image', 'runtime_image', 'binary_sha256',
    'gateway_url', 'gateway_ipv4', 'model', 'model_revision', 'context', 'output',
    'storage_class', 'workspace_gib', 'state_gib', 'deployment_revision', 'eval_suite_sha256',
}
IMAGE = r'[a-zA-Z0-9][a-zA-Z0-9._:/-]+@sha256:[0-9a-f]{64}'
EXAMPLE = {
    'schema_version': 1, 'workspace_id': 'pilot-dev01', 'image': '',
    'runtime_image': '', 'binary_sha256': '',
    'gateway_url': 'https://inference.example.invalid/v1', 'gateway_ipv4': '10.77.0.10',
    'model': 'REPLACE_WITH_APPROVED_MODEL', 'model_revision': '',
    'context': 32768, 'output': 8192, 'storage_class': '',
    'workspace_gib': 10, 'state_gib': 2, 'deployment_revision': '', 'eval_suite_sha256': '',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def parse_json(raw):
    require(len(raw) <= 1024 * 1024, 'JSON document too large')
    return json.loads(raw, object_pairs_hook=object_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))


def read_limited(path, limit):
    with pathlib.Path(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'Input file too large')
    return raw


def read_json(path):
    return parse_json(read_limited(path, 1024 * 1024))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) and value != '0' * 64


def pinned_image(value):
    return isinstance(value, str) and re.fullmatch(IMAGE, value) and sha(value.rsplit(':', 1)[1])


def text_field(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}', value))


def integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def validate_profile(p, final=True):
    require(isinstance(p, dict) and set(p) == FIELDS, 'Unexpected/missing profile fields')
    require(type(p['schema_version']) is int and p['schema_version'] == 1, 'Unsupported profile version')
    require(isinstance(p['workspace_id'], str) and
            re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?', p['workspace_id']), 'Invalid workspace ID')
    require(pinned_image(p['runtime_image']), 'Runtime base image must be pinned by digest')
    require(pinned_image(p['image']) if final else p['image'] == '' or pinned_image(p['image']),
            'Workspace image must be pinned by digest')
    require(sha(p['binary_sha256']), 'Expected binary SHA-256 required')
    require(sha(p['eval_suite_sha256']), 'Approved private eval suite SHA-256 required')
    require(isinstance(p['gateway_url'], str), 'Invalid gateway URL')
    u = urlsplit(p['gateway_url'])
    require(u.scheme == 'https' and u.path == '/v1' and not u.query and not u.fragment
            and not u.username and not u.password and u.port in (None, 443), 'Gateway must be HTTPS /v1 on port 443')
    require(u.hostname and '.' in u.hostname and
            re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', u.hostname) and
            len(u.hostname) <= 253 and all(0 < len(label) <= 63 for label in u.hostname.split('.')) and
            not u.hostname.endswith(('.invalid', '.localhost', '.example')), 'A real approved gateway hostname is required')
    require(p['gateway_url'] == f'https://{u.hostname}/v1', 'Use the canonical gateway URL without an explicit port')
    require(isinstance(p['gateway_ipv4'], str), 'Invalid gateway IPv4')
    address = ipaddress.IPv4Address(p['gateway_ipv4'])
    require(any(address in ipaddress.ip_network(net) for net in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')),
            'Gateway must use an approved RFC1918 IPv4 address for this MVP profile')
    require(text_field(p['model']) and not p['model'].startswith('REPLACE'), 'Approved model ID required')
    require(text_field(p['model_revision']) and p['model_revision'] not in ('latest', 'main', 'dev'), 'Pinned model revision required')
    require(text_field(p['deployment_revision']), 'Deployment integration revision required')
    require(isinstance(p['storage_class'], str) and re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,62}', p['storage_class']), 'Storage class required')
    require(integer(p['context'], 4096, 1048576), 'Invalid context limit')
    require(integer(p['output'], 1, min(p['context'], 32768)), 'Invalid output limit')
    require(integer(p['workspace_gib'], 1, 1024) and integer(p['state_gib'], 1, 128), 'Invalid storage limits')
    return p


def policy(p):
    return {'baseURL': p['gateway_url'], 'model': p['model'], 'context': p['context'], 'output': p['output']}


def write_new(path, value):
    path = pathlib.Path(path)
    with path.open('x', encoding='utf-8') as stream:
        path.chmod(0o600)
        stream.write(value)


def image_context(p, binary, output):
    validate_profile(p, final=False)
    binary = pathlib.Path(binary)
    require(binary.is_file() and not binary.is_symlink(), 'Binary must be a regular file')
    # Stream hashes so the compiled binary does not need a second in-memory copy.
    with binary.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    require(actual == p['binary_sha256'], 'Binary checksum mismatch')
    output = pathlib.Path(output)
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    shutil.copyfile(binary, output / 'opencode')
    with (output / 'opencode').open('rb') as stream:
        require(hashlib.file_digest(stream, 'sha256').hexdigest() == p['binary_sha256'], 'Copied binary checksum mismatch')
    (output / 'opencode').chmod(0o755)
    write_new(output / 'enterprise.json', json.dumps(policy(p), indent=2) + '\n')
    root = pathlib.Path(__file__).resolve().parents[1]
    shutil.copyfile(root / 'LICENSE', output / 'LICENSE')
    dockerfile = f'''FROM {p['runtime_image']}
USER 0
RUN mkdir -p /etc/opencode /workspace /home/opencode /tmp /usr/share/licenses/opencode \\
    && chmod 0755 /etc/opencode \\
    && chown 10001:10001 /workspace /home/opencode
COPY --chown=0:0 --chmod=0755 opencode /usr/local/bin/opencode
COPY --chown=0:0 --chmod=0644 enterprise.json /etc/opencode/enterprise.json
COPY --chown=0:0 --chmod=0644 LICENSE /usr/share/licenses/opencode/LICENSE
ENV HOME=/home/opencode XDG_CONFIG_HOME=/home/opencode/.config XDG_DATA_HOME=/home/opencode/.local/share XDG_CACHE_HOME=/home/opencode/.cache
USER 10001:10001
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/opencode"]
'''
    write_new(output / 'Dockerfile', dockerfile)


def timestamp(value):
    require(isinstance(value, str) and value.endswith('Z'), 'Timestamps must use UTC Z format')
    return dt.datetime.fromisoformat(value[:-1] + '+00:00')


def check_report(p, report, now=None):
    validate_profile(p)
    now = now or dt.datetime.now(dt.timezone.utc)
    require(isinstance(report, dict) and type(report.get('schema_version')) is int and report['schema_version'] == 1 and
            report.get('decision') == 'pass', 'Private eval has not passed')
    require(report.get('subject') == {'profile_sha256': digest(canonical(p)), 'image': p['image'],
                                     'binary_sha256': p['binary_sha256']}, 'Report does not match this deployment profile')
    issued, expires = timestamp(report.get('issued_at')), timestamp(report.get('expires_at'))
    require(issued <= now < expires and dt.timedelta(0) < expires - issued <= dt.timedelta(days=30),
            'Report is expired, future-dated or valid for more than 30 days')
    require(text_field(report.get('suite_version')) and report.get('suite_sha256') == p['eval_suite_sha256'] and
            text_field(report.get('evaluation_owner')), 'Private suite identity and owner required')
    require(type(report.get('unresolved_critical')) is int and report['unresolved_critical'] == 0 and
            type(report.get('unresolved_high')) is int and report['unresolved_high'] == 0,
            'Unresolved high/critical findings block acceptance')
    require(report.get('waivers') == [], 'This MVP does not accept gate waivers')
    gates = report.get('gates')
    require(isinstance(gates, dict) and set(gates) == set(GATES), 'Complete gate coverage is required')
    for name in GATES:
        gate = gates[name]
        require(isinstance(gate, dict) and gate.get('status') == 'pass' and
                integer(gate.get('executed'), 1, 10000000) and
                type(gate.get('failed')) is int and gate['failed'] == 0 and
                type(gate.get('skipped')) is int and gate['skipped'] == 0 and sha(gate.get('evidence_sha256')),
                'A required gate failed, was skipped or lacks evidence: ' + name)
    return report


def verify_report(p, report_path, signature_path, key_path):
    # Verify the exact byte snapshot we subsequently parse; do not read the report twice.
    import tempfile
    raw = read_limited(report_path, 1024 * 1024)
    signature = read_limited(signature_path, 64)
    require(len(signature) == 64, 'Expected an Ed25519 detached signature')
    key = read_limited(key_path, 16384)
    with tempfile.TemporaryDirectory(prefix='opencode-eval-') as tmp:
        tmp = pathlib.Path(tmp)
        for name, content in [('report', raw), ('signature', signature), ('key.pem', key)]:
            (tmp / name).write_bytes(content)
        public = subprocess.run(['openssl', 'pkey', '-pubin', '-in', str(tmp / 'key.pem'), '-text', '-noout'],
                                capture_output=True, check=False, timeout=10)
        require(public.returncode == 0 and b'ED25519' in public.stdout.upper(), 'An approved Ed25519 public key is required')
        result = subprocess.run(['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', str(tmp / 'key.pem'),
                                 '-rawin', '-in', str(tmp / 'report'), '-sigfile', str(tmp / 'signature')],
                                capture_output=True, check=False, timeout=10)
        require(result.returncode == 0, 'Private eval signature verification failed')
    return check_report(p, parse_json(raw))


def manifests(p, stage, report_sha=None):
    validate_profile(p)
    require(stage in ('evaluation', 'accepted'), 'Invalid stage')
    require(stage != 'accepted' or sha(report_sha), 'Accepted manifest requires verified report identity')
    namespace = 'opencode-' + p['workspace_id']
    labels = {'app.kubernetes.io/name': 'opencode-enterprise', 'opencode.stage': stage}
    annotations = {'opencode.profile-sha256': digest(canonical(p)), 'opencode.policy-sha256': digest(canonical(policy(p)))}
    if report_sha:
        annotations['opencode.eval-sha256'] = report_sha
    objects = [{'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': namespace,
                'labels': {'pod-security.kubernetes.io/enforce': 'restricted'}}},
        {'apiVersion': 'networking.k8s.io/v1', 'kind': 'NetworkPolicy', 'metadata': {'name': 'workspace-egress', 'namespace': namespace},
         'spec': {'podSelector': {}, 'policyTypes': ['Ingress', 'Egress'], 'ingress': [], 'egress': [
             {'to': [{'ipBlock': {'cidr': p['gateway_ipv4'] + '/32'}}], 'ports': [{'protocol': 'TCP', 'port': 443}]}]}}]
    for name, size in [('workspace', p['workspace_gib']), ('state', p['state_gib'])]:
        objects.append({'apiVersion': 'v1', 'kind': 'PersistentVolumeClaim',
            'metadata': {'name': name, 'namespace': namespace}, 'spec': {'accessModes': ['ReadWriteOnce'],
             'storageClassName': p['storage_class'], 'resources': {'requests': {'storage': f'{size}Gi'}}}})
    objects.append({'apiVersion': 'v1', 'kind': 'Pod', 'metadata': {'name': 'workspace', 'namespace': namespace,
        'labels': labels, 'annotations': annotations}, 'spec': {
        'automountServiceAccountToken': False, 'enableServiceLinks': False,
        'hostNetwork': False, 'hostPID': False, 'hostIPC': False,
        'dnsPolicy': 'None', 'dnsConfig': {'nameservers': ['127.0.0.1']},
        'hostAliases': [{'ip': p['gateway_ipv4'], 'hostnames': [urlsplit(p['gateway_url']).hostname]}],
        'securityContext': {'runAsNonRoot': True, 'runAsUser': 10001, 'runAsGroup': 10001,
                            'fsGroup': 10001, 'seccompProfile': {'type': 'RuntimeDefault'}},
        'containers': [{'name': 'agent', 'image': p['image'], 'imagePullPolicy': 'IfNotPresent',
            'command': ['/bin/sleep', 'infinity'], 'securityContext': {'allowPrivilegeEscalation': False,
                'readOnlyRootFilesystem': True, 'capabilities': {'drop': ['ALL']}},
            'resources': {'requests': {'cpu': '1', 'memory': '2Gi'},
                          'limits': {'cpu': '4', 'memory': '8Gi', 'ephemeral-storage': '10Gi'}},
            'volumeMounts': [{'name': 'workspace', 'mountPath': '/workspace'},
                {'name': 'state', 'mountPath': '/home/opencode'}, {'name': 'tmp', 'mountPath': '/tmp'}]}],
        'volumes': [{'name': name, 'persistentVolumeClaim': {'claimName': name}} for name in ('workspace', 'state')]
                   + [{'name': 'tmp', 'emptyDir': {'sizeLimit': '2Gi'}}]}})
    return objects


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init'); init.add_argument('--output', required=True)
    preflight = commands.add_parser('preflight'); preflight.add_argument('--profile', required=True)
    context = commands.add_parser('image-context')
    for name in ('profile', 'binary', 'output'): context.add_argument('--' + name, required=True)
    render = commands.add_parser('render')
    render.add_argument('--stage', choices=('evaluation', 'accepted'), required=True)
    render.add_argument('--profile', required=True); render.add_argument('--output', required=True)
    verify = commands.add_parser('verify-eval'); verify.add_argument('--profile', required=True)
    for command in (render, verify):
        for name in ('report', 'signature', 'trusted-key'):
            command.add_argument('--' + name, required=command is verify)
    args = parser.parse_args()
    if args.command == 'init':
        write_new(args.output, json.dumps(EXAMPLE, indent=2) + '\n')
        print('Unconfigured private profile created; edit it before preflight.')
        return
    p = read_json(args.profile)
    if args.command == 'image-context':
        image_context(p, args.binary, args.output)
        print('Image context prepared; build/scan/sign it, then set the resulting image digest in the profile.')
        return
    validate_profile(p)
    if args.command == 'preflight':
        print(json.dumps({'configuration': 'valid', 'profile_sha256': digest(canonical(p)),
                          'deployment_acceptance': 'not_evaluated'}))
        return
    report = None
    if args.command == 'verify-eval' or args.stage == 'accepted':
        require(args.report and args.signature and args.trusted_key, 'Signed private report and out-of-band trusted key required')
        report = verify_report(p, args.report, args.signature, args.trusted_key)
    if args.command == 'verify-eval':
        print('Signed evaluation matches this profile and satisfies the report gate. Customer deployment approval remains required.')
        return
    output = pathlib.Path(args.output)
    output.mkdir(mode=0o700, exist_ok=False)
    objects = manifests(p, args.stage, digest(canonical(report)) if report else None)
    write_new(output / '01-foundation.json', json.dumps({'apiVersion': 'v1', 'kind': 'List', 'items': objects[:-1]}, indent=2) + '\n')
    write_new(output / '02-workspace.json', json.dumps(objects[-1], indent=2) + '\n')
    print('Apply foundation first, verify CNI/admission/storage, then workspace. No resources were deployed by this command.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print('BLOCKED: ' + str(error), file=sys.stderr)
        sys.exit(1)
