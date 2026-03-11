CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS market_ticks (
  id BIGSERIAL PRIMARY KEY,
  event_ts TIMESTAMPTZ NOT NULL,
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  source TEXT NOT NULL,
  price DOUBLE PRECISION,
  bid DOUBLE PRECISION,
  ask DOUBLE PRECISION,
  volume DOUBLE PRECISION,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('market_ticks', 'event_ts', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_market_ticks_symbol_ts ON market_ticks (symbol, event_ts DESC);
CREATE INDEX IF NOT EXISTS idx_market_ticks_exchange_ts ON market_ticks (exchange, event_ts DESC);

CREATE TABLE IF NOT EXISTS documents (
  id BIGSERIAL PRIMARY KEY,
  source_type TEXT NOT NULL,
  source TEXT NOT NULL,
  url TEXT NOT NULL,
  title TEXT NOT NULL,
  content_text TEXT NOT NULL,
  timeline_tag TEXT NOT NULL CHECK (timeline_tag IN ('past', 'present', 'future')),
  asset_tags TEXT[] NOT NULL DEFAULT '{}',
  confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  content_hash TEXT NOT NULL UNIQUE,
  published_at TIMESTAMPTZ,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  raw_object_key TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_timeline ON documents (timeline_tag, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_asset_tags ON documents USING GIN (asset_tags);
CREATE INDEX IF NOT EXISTS idx_documents_published ON documents (published_at DESC);

CREATE TABLE IF NOT EXISTS audit_events (
  id BIGSERIAL PRIMARY KEY,
  event_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  service TEXT NOT NULL,
  action TEXT NOT NULL,
  status TEXT NOT NULL,
  correlation_id TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_audit_events_ts ON audit_events (event_ts DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_service_ts ON audit_events (service, event_ts DESC);
