"""Sealed-inventory readiness and isolated parallel evaluation, never promotion."""
import argparse
import hashlib
import json
import sys
import time
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.research import cmc_bounded_adapter as adapter
from scripts.research import cmc_bounded_daily as calculator
from scripts.research.cmc_snapshot_inventory import digest, verified_manifest


def run(seal_path, expected_sha256, *, now_ms, evaluate=False):
    seal_path = Path(seal_path)
    raw = seal_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('seal differs from independently recorded anchor')
    seal = json.loads(raw)
    manifest = verified_manifest(seal_path, now_ms=now_ms)
    if digest(seal_path) != expected_sha256:
        raise ValueError('seal changed during verification')
    mature_at = calculator.boundary_ms(calculator.START + timedelta(days=calculator.DAYS-1))
    report = {'artifact_type': 'PARALLEL_BOUNDED_STUDY_WORKFLOW',
              'status': 'MATURE_INPUT_CHECK_NOT_PERFORMED' if now_ms >= mature_at else 'WAITING_FOR_DECLARED_MATURITY',
              'as_of_ms': now_ms, 'not_before_ms': mature_at,
              'published_files': len(seal['files']), 'v3_manifest_entries': len(manifest),
              'seal_sha256': expected_sha256, 'scoring_authorized': False,
              'source_authentication': 'UNVERIFIED',
              'inventory_scope': 'CURRENT_DECLARED_FOLDER_MATCHES_RECORDED_SEAL',
              'past_completeness_before_baseline': 'UNVERIFIED',
              'qualification_verified': False, 'market_outcomes_evaluated': False,
              'contract_sha256': digest(calculator.CONTRACT),
              'implementation_sha256': digest(__file__),
              'dependency_sha256': {'adapter': digest(adapter.__file__),
                                    'calculator': digest(calculator.__file__)}}
    if not evaluate:
        return report
    if now_ms < mature_at:
        raise ValueError('declared window not mature; no outcome evaluation allowed')
    audit = adapter.build(manifest, now_ms=now_ms)
    result = calculator.evaluate(audit, now_ms=now_ms)
    # Detect observed inventory/source changes during composition; not an atomic snapshot.
    if verified_manifest(seal_path, now_ms=now_ms) != manifest or digest(seal_path) != expected_sha256:
        raise ValueError('sealed evidence changed during composition')
    report.update(status='DESCRIPTIVE_PARALLEL_RESULT', market_outcomes_evaluated=True,
                  audit=audit, result=result)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seal', type=Path, required=True)
    p.add_argument('--seal-sha256', required=True, help='Anchor from recorded inventory review; not recomputed silently.')
    p.add_argument('--evaluate', action='store_true', help='Explicit mature parallel analysis, never original scoring.')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        saved = json.loads(args.seal.read_bytes())
        if args.output is not None:
            root = Path(saved['directory']).resolve()
            output = args.output.resolve()
            if output == root or root in output.parents:
                raise ValueError('report must be outside snapshot directory')
            if output.exists():
                raise FileExistsError('report exists; original evidence cannot be overwritten')
        result = run(args.seal, args.seal_sha256, now_ms=int(time.time()*1000), evaluate=args.evaluate)
        if args.output is not None:
            with args.output.open('x', encoding='utf-8') as stream:
                json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write('\n')
        print(json.dumps({k: result[k] for k in ('status', 'published_files', 'v3_manifest_entries',
                                               'market_outcomes_evaluated', 'scoring_authorized')}))
        return 0
    except (ValueError, OSError, KeyError, TypeError, OverflowError) as exc:
        print(json.dumps({'status': 'INCOMPLETE', 'reason': str(exc), 'scoring_authorized': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
