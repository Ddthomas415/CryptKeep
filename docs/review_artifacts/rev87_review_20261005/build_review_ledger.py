"""Preserve explicit reviewed and unread states for every unique archive member."""
import csv
import json
import re
from pathlib import Path

source = Path('/private/tmp/cryptkeep-shared-unique-20261005/coverage.json')
output = Path(__file__).parent
items = json.loads(source.read_text())
read_hashes = {
    'f57f541cb16f7736', '26a6919d128c8637', '4d48268b8d8ba53d',
    '64af9a37197fc1f4', 'd88a57c07c1976a1', 'dd95fdbe6c8235bf',
    '60550d00e600f335',
}
execution_folders = {
    '55_clock_measurement_quality', '63_spot_only_order_boundary',
    '64_order_gates_cannot_pass_blind', '66_executor_reconcile_partial_fills',
    '67_fill_sink_loss_lock_and_risk_write', '70_killswitch_cli_records',
    '73_risk_sink_flag_clear', '77_live_enable_rollback',
    '78_symbol_lock_at_order_boundary', '79_boundary_refusal_in_consumer',
    '80_adapter_unavailable_in_consumer',
}
research_folders = {
    '56_end_to_end_pipeline_test', '57_sweep_holdout_and_effect',
    '58_ohlcv_preflight_rejection', '59_fill_slippage_measurement',
    '60_funding_join_coverage', '61_crypto_edge_capture_time',
    '62_edge_cadence_source_and_gaps', '71_capped_live_gate_scope',
    '72_stored_only_risk_labels', '74_test_suite_state_isolation',
    '75_outcomes_follow_state_dir', '76_paper_stop_scoped',
}
support = output / 'supporting_documents_review.md'
for batch_report in sorted(output.glob('remaining_batch_*_review.md')):
    read_hashes.update(value[:16] for value in re.findall(
        r'^\|[^\n]*?`([0-9a-f]{64})`', batch_report.read_text(), re.MULTILINE
    ))
config_csv = output / 'config_and_csv_review.md'
for parent_report in (config_csv, output / 'bounded_early_patch_review.md', output / 'early_dependency_continuation_review.md', output / 'entry_exit_dependency_diff_review.md', output / 'entry_exit_complete_patch_review.md', output / 'journal_prototype_contract_review.md', output / 'journal_extension_complete_review.md', output / 'journal_support_probes_review.md', output / 'runner_journal_correction_probe_review.md', output / 'venue_safety_diff_review.md'):
    if parent_report.exists():
        read_hashes.update(value[:16] for value in re.findall(r'^\| `([0-9a-f]{64})` \|', parent_report.read_text(), re.MULTILINE))
reconciler = output / 'reconciler_complete_artifact_review.md'
if reconciler.exists():
    artifact_table = reconciler.read_text().split('## Exact Artifact Paths and SHA-256', 1)[1].split('## Candidate', 1)[0]
    read_hashes.update(value[:16] for value in re.findall(r'`([0-9a-f]{64})`', artifact_table))
if support.exists():
    for line in support.read_text().splitlines():
        if line.startswith('| S'):
            matches = re.findall(r'`([0-9a-f]{64})`', line)
            read_hashes.update(value[:16] for value in matches)
with (output / 'shared_file_coverage.csv').open('w', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['sha256', 'bytes', 'coverage', 'evidence', 'archive_references'])
    for item in items:
        status = 'INVENTORIED_NOT_SEMANTICALLY_REVIEWED'
        evidence = 'Byte inventory only; not acceptance proof'
        names = [r['member'] for r in item['references']]
        if item['sha256'][:16] in read_hashes:
            status = 'READ_FULL_CONTENT'
            evidence = 'Parent review; spreadsheet XML cells/formulas, not recalculation or visual QA'
        if any(n.endswith('/MANIFEST.txt') for n in names):
            status = 'HISTORICAL_DIFF_READ'
            evidence = 'All revision 58-87 manifest evolution diffs read; latest full text separately reviewed'
        for name in names:
            parts = name.split('/')
            folder = parts[1] if len(parts) > 2 else ''
            prefix = folder.split('_', 1)[0]
            if name.endswith('/REVIEW_HANDOFF.md') or (
                name.endswith('/README.txt') and prefix.isdigit() and 17 <= int(prefix) <= 54
            ):
                status = 'READ_FULL_CONTENT'
                evidence = 'Fermat document review; historical claims not independently reproduced'
            if folder in {'68_dead_man_names_per_host', '69_ci_runs_slow_tests'} and (
                name.endswith('/README.txt') or name.endswith('/production_files_only.diff')
                or re.search(r'/(0060|0061)-[^/]+\.patch$', name)
            ):
                status = 'READ_FULL_CONTENT'
                evidence = 'Fermat full README/patch/diff inspection; no host or CI proof'
            if (output / 'specialist_execution_review.md').exists() and folder in execution_folders and (
                name.endswith('/README.txt') or name.endswith('/production_files_only.diff')
                or re.search(r'/\d{4}-[^/]+\.patch$', name)
            ):
                status = 'READ_FULL_CONTENT'
                evidence = 'Specialist execution review; findings remain unresolved'
            if (output / 'specialist_research_review.md').exists() and folder in research_folders and (
                name.endswith('/README.txt') or name.endswith('/production_files_only.diff')
                or re.search(r'/\d{4}-[^/]+\.patch$', name)
            ):
                status = 'READ_FULL_CONTENT'
                evidence = 'Specialist research review; source-only probes, not pytest or host proof'
        if item['extracted'].endswith(('.json', '.jsonl', '.sqlite')) and status == 'INVENTORIED_NOT_SEMANTICALLY_REVIEWED':
            status = 'STRUCTURAL_VALIDATION_ONLY'
            evidence = 'JSON parse or SQLite integrity only; semantic review not complete'
        writer.writerow([item['sha256'], item['size'], status, evidence,
                         json.dumps(item['references'], separators=(',', ':'))])
print(f'Wrote explicit coverage for {len(items)} unique archive contents')
historical = output / 'historical_submission_inventory.json'
report = output / 'historical_documents_review.md'
if historical.exists() and report.exists():
    with (output / 'shared_file_coverage.csv').open() as stream:
        latest = {row['sha256']: row for row in csv.DictReader(stream)}
    reviewed = set(re.findall(
        r'SHA256: `([0-9a-f]{64})`\. Bytes: \d+\. Coverage: FULL_TEXT_READ', report.read_text()
    ))
    supporting_history = output / 'historical_support_artifacts_review.md'
    historical_code = output / 'historical_code_review.md'
    if historical_code.exists():
        reviewed.update(re.findall(r'^- SHA-256: `([0-9a-f]{64})`;', historical_code.read_text(), re.MULTILINE))
    if supporting_history.exists():
        for line in supporting_history.read_text().splitlines():
            if re.match(r'\| (PY\d|CFG\d|XLS\d) \|', line):
                reviewed.update(re.findall(r'`([0-9a-f]{64})`', line))
    with (output / 'all_review_family_coverage.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['sha256', 'bytes', 'coverage', 'evidence', 'archive_references'])
        for item in json.loads(historical.read_text())['unique_contents']:
            row = latest.get(item['sha256'])
            status = row['coverage'] if row else 'INVENTORIED_NOT_SEMANTICALLY_REVIEWED'
            evidence = row['evidence'] if row else 'Historical-only code/data; not reviewed in documentary sidecar'
            if item['sha256'] in reviewed:
                status = 'READ_FULL_CONTENT'
                evidence = 'Historical sidecar full-content inspection; not current runtime acceptance'
            if item['sha256'].startswith('eb24c68703319a3f'):
                status = 'PARTIALLY_READ'
                evidence = 'Historical work log lines 1-1050 and 42240-42325 read; remaining ranges not fully reviewed'
            if any(Path(r['member']).name.startswith('trace_') for r in item['references']):
                status = 'SUPPLIED_OUTPUT_COMPARED'
                evidence = 'All 75 scenario objects compared; original generation not reproduced, latest trace ends at 0028'
            writer.writerow([item['sha256'], item['bytes'], status, evidence,
                             json.dumps(item['references'], separators=(',', ':'))])
    print(f'Historical documentary full-read hashes: {len(reviewed)}')
