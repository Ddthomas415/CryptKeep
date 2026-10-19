"""Value-free metadata comparisons; no Docker, credentials or gate changes.

An optional reviewed profile binds expected public metadata to the existing plan
fingerprints. Only fixed field names and booleans may leave the comparison child.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from scripts.research import companion_runtime_adapter as adapter
from scripts.research import companion_network_configuration as network

FIELDS = ("mounts", "ports", "entrypoint", "command", "healthcheck", "workdir",
          "extra_hosts", "dns", "dns_search", "dns_options", "network_mode",
          "networks", "flags", *adapter.RECREATION_FIELDS)
SCHEMA = 'companion-metadata-diagnostics-v1'
REPORT = 'companion-metadata-comparison-v1'
SHA = re.compile(r'[0-9a-f]{64}\Z')


def refuse():
    raise ValueError('metadata_diagnostics_refused') from None


def fingerprint(row, bindings):
    return network.project(row, bindings)[0] if bindings else adapter.preservation_digest(row)


def _flags(row):
    flags = row.get('flags')
    allowed = set(adapter.ENV_EXPECTED) | adapter.SECRET_PRESENCE
    if type(flags) is not list or len(flags) > len(allowed) + 1:
        refuse()
    for flag in flags:
        if flag is not None and (type(flag) is not dict or set(flag) != {'key', 'ok'}
                or flag['key'] not in allowed or type(flag['ok']) is not bool):
            refuse()
    return flags


def project_replacement(row):
    expected = {field: copy.deepcopy(row.get(field)) for field in FIELDS}
    overrides = set(adapter.ENV_EXPECTED) - {'POSTGRES_USER', 'POSTGRES_DB'}
    flags = [dict(f) for f in _flags(row) if f is not None]
    present = set()
    for flag in flags:
        if flag['key'] in overrides:
            flag['ok'] = True
        present.add(flag['key'])
    flags.extend({'key': key, 'ok': True} for key in adapter.ENV_EXPECTED
                 if key in overrides and key not in present)
    expected['flags'] = [*flags, None]
    return expected


def make_profile(plan, plan_sha256, observations):
    """Derive from saved public observations and require existing gate parity."""
    if not SHA.fullmatch(plan_sha256) or type(observations) is not list or len(observations) != 7:
        refuse()
    by_name = {r['name'].removeprefix('/'): r for r in observations}
    if set(by_name) != {r.name for r in plan.baseline}:
        refuse()
    bindings = dict(plan.network_bindings)
    applications = []
    for before in plan.baseline[3:]:
        row = by_name[before.name]
        if (row.get('id') != before.id or row.get('image') != before.image
                or adapter.preservation_digest(row) != before.metadata
                or (bindings and fingerprint(row, bindings) != before.configured_metadata)):
            refuse()
        applications.append({'name': before.name, 'expected': project_replacement(row)})
    result = {'schema': SCHEMA, 'plan_sha256': plan_sha256, 'applications': applications}
    raw = json.dumps(result, sort_keys=True, separators=(',', ':')).encode()
    Expectations.load(raw, hashlib.sha256(raw).hexdigest(), plan, plan_sha256)
    return result


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            refuse()
        result[key] = value
    return result


@dataclass(frozen=True)
class Expectations:
    applications: tuple
    bindings: tuple

    @classmethod
    def load(cls, raw, trusted_sha256, plan, plan_sha256):
        try:
            if (type(raw) is not bytes or len(raw) > 1_048_576
                    or not SHA.fullmatch(trusted_sha256)
                    or hashlib.sha256(raw).hexdigest() != trusted_sha256):
                refuse()
            data = json.loads(raw, object_pairs_hook=_unique)
            if (set(data) != {'schema', 'plan_sha256', 'applications'} or data['schema'] != SCHEMA
                    or data['plan_sha256'] != plan_sha256
                    or [a['name'] for a in data['applications']] != [a['name'] for a in plan.applications]):
                refuse()
            bindings = dict(plan.network_bindings)
            for record, app in zip(data['applications'], plan.applications):
                if set(record) != {'name', 'expected'} or set(record['expected']) != set(FIELDS):
                    refuse()
                _flags(record['expected'])
                key = 'replacement_configured_metadata' if bindings else 'replacement_metadata'
                if fingerprint(record['expected'], bindings) != app[key]:
                    refuse()
            return cls(tuple(data['applications']), plan.network_bindings)
        except Exception:
            refuse()

    def compare(self, name, observed, observed_digest):
        bindings = dict(self.bindings)
        expected = next(a['expected'] for a in self.applications if a['name'] == name)
        _flags(observed)
        left, right = fingerprint(expected, bindings), fingerprint(observed, bindings)
        if right != observed_digest:
            refuse()
        fields = {}
        for field in FIELDS:
            # Use both directions of the unchanged gate, including its normalization.
            a, b = {**expected, field: observed.get(field)}, {**observed, field: expected.get(field)}
            fields[field] = fingerprint(a, bindings) == left and fingerprint(b, bindings) == right
        flags_left = sorted(json.dumps(f, sort_keys=True) for f in _flags(expected))
        flags_right = sorted(json.dumps(f, sort_keys=True) for f in _flags(observed))
        return validate_report({'schema': REPORT, 'available': True,
            'aggregate_matches': left == right, 'fields': fields,
            'flags_order_only': expected['flags'] != observed.get('flags') and flags_left == flags_right,
            'interaction_unresolved': left != right and all(fields.values())})


def unavailable():
    return {'schema': REPORT, 'available': False}


def validate_report(report):
    if type(report) is not dict:
        refuse()
    if report == unavailable():
        return unavailable()
    keys = {'schema', 'available', 'aggregate_matches', 'fields', 'flags_order_only', 'interaction_unresolved'}
    if (set(report) != keys or report['schema'] != REPORT or report['available'] is not True
            or type(report['fields']) is not dict or set(report['fields']) != set(FIELDS)
            or any(type(v) is not bool for v in report['fields'].values())
            or any(type(report[k]) is not bool for k in ('aggregate_matches', 'flags_order_only', 'interaction_unresolved'))):
        refuse()
    return copy.deepcopy(report)


def read_profile(path, trusted_sha256, plan, plan_sha256):
    """Only an explicit reviewed public artifact may be used by the installer."""
    import os
    import stat
    root = Path(__file__).resolve().parents[2] / 'docs/review_artifacts'
    path = Path(path).absolute()
    if path.suffix != '.json' or not path.is_relative_to(root) or path.resolve(strict=True) != path:
        refuse()
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            refuse()
        raw = stream.read(1_048_577)
    return Expectations.load(raw, trusted_sha256, plan, plan_sha256)


def main():
    from scripts.research.companion_installer import Plan
    parser = argparse.ArgumentParser(description='Offline public diagnostic profile; no installer invocation')
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--reviewed-manifest-sha256', required=True)
    parser.add_argument('--observation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.manifest.read_bytes()
    plan = Plan.load(raw, args.reviewed_manifest_sha256)
    observation = json.loads(args.observation.read_bytes())
    profile = make_profile(plan, args.reviewed_manifest_sha256, observation['observations'])
    output = (json.dumps(profile, indent=2, sort_keys=True) + '\n').encode()
    with args.output.open('xb') as stream:
        stream.write(output)
    print(json.dumps({'state': 'READY_FOR_INDEPENDENT_REVIEW', 'profile_sha256': hashlib.sha256(output).hexdigest(),
                      'applications': len(profile['applications']), 'runtime_actions': False}))


if __name__ == '__main__':
    main()
