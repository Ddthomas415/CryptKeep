from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

from services.analytics.paper_campaign_recovery import load_campaign_specs
from services.audit.operator_event_journal import OperatorEventJournalError, append_operator_event
from services.os.app_paths import code_root


class CampaignManifestUpdateError(ValueError):
    """Raised when a campaign manifest update request is invalid."""


def _repo_relative(path: Path) -> str:
    root = code_root().resolve()
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(root))
    except ValueError:
        return str(resolved)


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise CampaignManifestUpdateError(f"manifest_read_failed:{type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise CampaignManifestUpdateError("manifest_not_object")
    if payload.get("schema_version") != 1:
        raise CampaignManifestUpdateError("unsupported_schema_version")
    campaigns = payload.get("campaigns")
    if not isinstance(campaigns, list):
        raise CampaignManifestUpdateError("campaigns_not_list")
    return payload


def _find_campaign(payload: dict[str, Any], name: str) -> tuple[int, dict[str, Any]]:
    for idx, row in enumerate(payload.get("campaigns") or []):
        if not isinstance(row, dict):
            raise CampaignManifestUpdateError("campaign_not_object")
        if str(row.get("name") or "").strip() == name:
            return idx, row
    raise CampaignManifestUpdateError("unknown_campaign")


def _campaign_state(*, manifest_path: Path, campaign: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": _repo_relative(manifest_path),
        "campaign": str(campaign.get("name") or ""),
        "enabled": bool(campaign.get("enabled", True)),
        "strategy": str(campaign.get("strategy") or ""),
        "session_strategy_id": str(campaign.get("session_strategy_id") or ""),
        "symbol": str(campaign.get("symbol") or ""),
        "venue": str(campaign.get("venue") or ""),
        "signal_source": str(campaign.get("signal_source") or ""),
    }


def _validate_after_payload(payload: dict[str, Any], manifest_path: Path) -> None:
    # Reuse the runtime loader so the governed writer cannot create a manifest
    # that the campaign restore/status path cannot read.
    tmp_path = manifest_path.with_suffix(manifest_path.suffix + ".tmp-validate")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    try:
        load_campaign_specs(tmp_path, repo_root=code_root())
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def update_campaign_enabled(
    *,
    manifest_path: Path,
    campaign_name: str,
    enabled: bool,
    actor: str = "operator",
    reason: str = "campaign_manifest_update",
    event_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    manifest = Path(manifest_path)
    name = str(campaign_name or "").strip()
    if not name:
        return {"ok": False, "changed": False, "reason": "missing_campaign"}

    try:
        before_payload = _load_manifest(manifest)
        idx, before_campaign = _find_campaign(before_payload, name)
        before_state = _campaign_state(manifest_path=manifest, campaign=before_campaign)
        after_payload = copy.deepcopy(before_payload)
        after_campaign = after_payload["campaigns"][idx]
        after_campaign["enabled"] = bool(enabled)
        after_state = _campaign_state(manifest_path=manifest, campaign=after_campaign)
        _validate_after_payload(after_payload, manifest)
    except CampaignManifestUpdateError as exc:
        return {"ok": False, "changed": False, "reason": str(exc)}
    except Exception as exc:
        return {"ok": False, "changed": False, "reason": f"manifest_validation_failed:{type(exc).__name__}:{exc}"}

    if before_state["enabled"] == after_state["enabled"]:
        return {
            "ok": True,
            "changed": False,
            "reason": "campaign_manifest_unchanged",
            "manifest": before_state["manifest"],
            "campaign": name,
            "enabled": after_state["enabled"],
        }

    event_target = f"paper_campaign_manifest:{before_state['manifest']}:{name}"
    if dry_run:
        return {
            "ok": True,
            "changed": False,
            "dry_run": True,
            "reason": "dry_run",
            "manifest": before_state["manifest"],
            "campaign": name,
            "pre_state": before_state,
            "post_state": after_state,
        }

    try:
        started_event = append_operator_event(
            actor=actor,
            action="campaign_manifest_change",
            target=event_target,
            result="started",
            reason=reason,
            pre_state=before_state,
            post_state=after_state,
            source="services.admin.campaign_manifest_audit",
            extra={"operation": "set_enabled"},
            path=event_path,
        )
    except OperatorEventJournalError as exc:
        return {
            "ok": False,
            "changed": False,
            "reason": "operator_event_write_failed_campaign_manifest_not_changed",
            "error": str(exc),
            "manifest": before_state["manifest"],
            "campaign": name,
        }

    try:
        _atomic_write_json(manifest, after_payload)
    except Exception as exc:
        return {
            "ok": False,
            "changed": False,
            "reason": f"manifest_write_failed:{type(exc).__name__}",
            "event_id": started_event.get("event_id"),
            "manifest": before_state["manifest"],
            "campaign": name,
        }

    completion_event: dict[str, Any] | None = None
    completion_error = ""
    try:
        completion_event = append_operator_event(
            actor=actor,
            action="campaign_manifest_change",
            target=event_target,
            result="succeeded",
            reason=reason,
            pre_state=before_state,
            post_state=after_state,
            source="services.admin.campaign_manifest_audit",
            extra={"operation": "set_enabled", "started_event_id": started_event.get("event_id")},
            path=event_path,
        )
    except OperatorEventJournalError as exc:
        completion_error = str(exc)

    return {
        "ok": True,
        "changed": True,
        "reason": "campaign_manifest_updated",
        "manifest": before_state["manifest"],
        "campaign": name,
        "enabled": after_state["enabled"],
        "event_id": started_event.get("event_id"),
        "completion_event_id": (completion_event or {}).get("event_id"),
        "completion_event_error": completion_error,
    }

