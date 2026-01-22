# Alerts Hardening (Phase 213)

## Fix
- place_order alert routing now passes cfg into _emit_order_event (no scope bug)

## Redaction
- Alert payloads are redacted in alert_router:
  - keys like secret/token/password/webhook are replaced with <redacted>
  - long strings and Slack webhook URLs are redacted

## Dry-run safety
- alerts.never_alert_on_dry_run: true (default)
- dry_run events will NOT alert unless the dry_run rule is explicitly enabled

## Health
- data/alerts_last.json stores the last send attempt result
- UI shows "Alert health (last send)" in Alerts Settings
