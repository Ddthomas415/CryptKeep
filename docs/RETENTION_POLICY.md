# Evidence And Runtime Retention Policy

Date: 2026-07-03
Status: policy baseline for paper/research operation

## Purpose

Define what CryptKeep keeps, what may be pruned, and what must not be deleted
without an accepted decision.

## Current Default

For paper/research operation, default to keep evidence artifacts indefinitely
unless storage pressure or privacy requirements force a narrower rule.

This is acceptable only while:

- disk monitoring exists on the operating host
- backups are planned before server migration becomes canonical
- logs are not shared externally without review
- secrets are not written to evidence artifacts

## Must Keep

Keep indefinitely unless a later accepted retention decision replaces this:

- promotion evidence JSONL
- strategy decision records
- work-log entries
- gate output checkpoints
- trade journal databases
- shadow would-be-fill evidence
- archive dataset manifests and hashes
- deployment/migration proof packets

## May Rotate

These can be rotated after they are no longer needed for incident review:

- debug logs
- transient status files
- dashboard cache artifacts
- old local notification reports
- temporary preflight outputs

Recommended minimum retention for rotated operational logs: 90 days.

## Must Not Keep

Do not intentionally retain:

- API secrets
- raw private keys
- exchange account tokens
- unredacted credential prompts
- sensitive provider responses not needed for evidence

If such material appears in a log or artifact, treat it as a security incident,
rotate the credential if applicable, and record the cleanup.

## Pruning Rule

No pruning command should delete canonical evidence by glob alone. A safe prune
must name:

- artifact family
- retention cutoff
- backup status
- dry-run output
- operator approval

## Server Migration Requirement

Before canonical server operation, add a host-specific retention packet covering:

- disk limit
- backup schedule
- restore drill
- log rotation mechanism
- alert threshold for storage pressure
