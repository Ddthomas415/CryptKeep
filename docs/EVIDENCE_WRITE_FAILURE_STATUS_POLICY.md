# CryptKeep Evidence-Write Failure Status Policy

Status: `POLICY_DOCUMENTED`

## Purpose

Define how evidence write failures must surface before paper, shadow, or live
promotion evidence can be trusted. This document does not implement counters or
session refusal behavior.

## Current Boundary

SHOWN:

- Promotion gates depend on JSONL and SQLite evidence artifacts.
- Operator status now reports provenance qualification details.
- The backlog already calls out silent evidence starvation as a launch-quality
  problem.

UNVERIFIED:

- Session status does not yet prove bounded evidence-write failure counters for
  every signal/fill/session writer.
- No refusal threshold has been executed against a repeated writer-failure
  fixture.

## Required Status Fields

Every long-running evidence campaign should expose:

- `evidence_write_failures_total`;
- `evidence_write_failures_consecutive`;
- `last_evidence_write_error_type`;
- `last_evidence_write_error_ts`;
- `last_successful_evidence_write_ts`;
- `evidence_writer_status`: `ok`, `degraded`, or `refusing`;
- `evidence_refusal_reason` when refusing.

## Refusal Policy

If evidence writes fail repeatedly while trading or paper simulation continues,
the system must fail closed for evidence-bearing operation:

- `ok`: zero recent failures or recovery after a bounded failure.
- `degraded`: transient failures below the refusal threshold; status visible.
- `refusing`: threshold reached; no new evidence-bearing session should be
  treated as valid until the writer recovers and the operator records review.

Refusal must not delete already-written evidence. It should prevent false
confidence from sessions that kept running while evidence was silently absent.

## Proof Required

Before capped live, add tests or an evidence packet showing:

- one injected signal-evidence write failure increments counters;
- repeated failures transition status to `refusing`;
- a recovered writer resets consecutive failures but preserves total failures;
- promotion status surfaces the failure/refusal reason;
- no gate treats a refusing evidence session as promotion-quality evidence.

