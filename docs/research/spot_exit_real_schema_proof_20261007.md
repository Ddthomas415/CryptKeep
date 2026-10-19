# Real-schema settlement and rollback proof

ENGINEER verification stage. Isolated9wbPbN only, no production source change.
New tests/test_spot_exit_real_schema.py uses actual ExecutionStore and
LivePositionStore schemas/APIs with temporary databases.

23 targeted tests passed0.36s including prior20 primitive tests.
- Partial0.2 fill on0.4 sell, cancellation, completed delivery and applied
  position fill permit one settlement; observed held quantity0.8, retry false.
- Unapplied canonical fill refuses settlement, retains reservation/no tombstone.
- SQLite BEFORE DELETE trigger raises ABORT after tombstone insertion; both
  operations roll back. Restart/reopen and retry after removing test trigger
  completes settlement. This is transaction error injection, not OS power loss.

Terminal receipt remains synthetically inserted by fixture. These tests do not
verify exchange-order identity binding or trusted receipt production. No claim
of venue integration, loss-lock bypass or fresh reconciled production account.
Next bounded implementation: receipt producer binds remote order ID to durable
intent/order mapping before admitting terminal evidence. No caller metadata
may independently authorize settlement.
Independent tests-only review requested; READY_FOR_INDEPENDENT_REVIEW.
