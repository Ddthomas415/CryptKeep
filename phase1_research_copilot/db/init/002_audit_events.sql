CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    event_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    correlation_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_audit_events_event_ts ON audit_events (event_ts DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_service ON audit_events (service);
CREATE INDEX IF NOT EXISTS idx_audit_events_action ON audit_events (action);
