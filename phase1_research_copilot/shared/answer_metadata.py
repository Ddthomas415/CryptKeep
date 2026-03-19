from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shared.models import AnswerMetadata


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def timestamp_age_seconds(value: Any) -> int | None:
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    return max(int((datetime.now(timezone.utc) - parsed).total_seconds()), 0)


def first_non_empty(*values: Any) -> str | None:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None


def freshness_status_from_label(label: Any) -> str:
    value = str(label or "").strip().lower()
    mapping = {
        "fresh": "fresh",
        "recent": "fresh",
        "aging": "aging",
        "stale": "stale",
        "missing": "missing",
        "no live data": "missing",
        "no freshness data": "missing",
        "unavailable": "missing",
        "unknown": "missing",
    }
    return mapping.get(value, "missing")


def freshness_label_from_timestamp(value: Any) -> str:
    age_seconds = timestamp_age_seconds(value)
    if age_seconds is None:
        return "Unknown"
    if age_seconds < 3600:
        return "Fresh"
    if age_seconds < 6 * 3600:
        return "Recent"
    if age_seconds < 24 * 3600:
        return "Aging"
    return "Stale"


def confidence_label(score: float | None) -> str:
    try:
        numeric = float(score)
    except (TypeError, ValueError):
        return "Unknown"
    if numeric >= 0.75:
        return "High"
    if numeric >= 0.45:
        return "Medium"
    return "Low"


def normalize_answer_metadata(payload: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(payload, dict):
        if "source_family" not in payload and ("source_label" in payload or "freshness" in payload or "freshness_label" in payload):
            source_type = str(payload.get("source_type") or "fallback")
            source_family = {
                "live_public_structural": "live_public",
                "cached_research": "cached_research",
                "market_snapshot": "market_context",
                "fallback": "fallback",
            }.get(source_type, "fallback")
            freshness_status = str(
                payload.get("freshness_status")
                or payload.get("freshness")
                or freshness_status_from_label(payload.get("freshness_label"))
            )
            data_timestamp = payload.get("data_timestamp")
            partial_provenance = bool(
                payload.get("partial_provenance")
                if "partial_provenance" in payload
                else not (source_type == "live_public_structural" and data_timestamp)
            )
            metadata_status = "ok"
            if source_type == "fallback" or freshness_status == "missing":
                metadata_status = "critical"
            elif partial_provenance or freshness_status in {"aging", "stale"}:
                metadata_status = "warn"
            payload = {
                "as_of": payload.get("as_of") or utc_now_iso(),
                "source_type": source_type,
                "source_family": source_family,
                "source_ids": list(payload.get("source_ids") or payload.get("source_names") or []),
                "freshness_status": freshness_status,
                "age_seconds": payload.get("age_seconds"),
                "confidence_label": payload.get("confidence_label") or "Unknown",
                "caveat": payload.get("caveat"),
                "partial_provenance": partial_provenance,
                "missing_provenance_reason": payload.get("missing_provenance_reason"),
                "source_name": payload.get("source_name") or payload.get("source_label"),
                "source_names": list(payload.get("source_names") or []),
                "data_timestamp": data_timestamp,
                "metadata_status": payload.get("metadata_status") or metadata_status,
            }
        return AnswerMetadata.model_validate(payload).model_dump()
    return fallback_answer_metadata()


def fallback_answer_metadata(*, reason: str | None = None) -> dict[str, Any]:
    reason_text = str(reason or "Explain provenance is unavailable.").strip()
    return AnswerMetadata(
        as_of=utc_now_iso(),
        source_type="fallback",
        source_family="fallback",
        source_ids=["gateway_fallback"],
        freshness_status="missing",
        age_seconds=None,
        confidence_label="Low",
        caveat="Research only. Execution disabled. Upstream explain context is unavailable.",
        partial_provenance=True,
        missing_provenance_reason=reason_text,
        source_name="Fallback",
        source_names=["Gateway Fallback"],
        data_timestamp=None,
        metadata_status="critical",
    ).model_dump()


def build_answer_metadata(
    tool_results: dict[str, Any],
    *,
    confidence: float,
) -> dict[str, Any]:
    market = tool_results.get("get_market_snapshot") if isinstance(tool_results.get("get_market_snapshot"), dict) else {}
    crypto_edges = (
        tool_results.get("get_crypto_edge_report")
        if isinstance(tool_results.get("get_crypto_edge_report"), dict)
        else {}
    )
    latest_live_edges = (
        tool_results.get("get_latest_live_crypto_edge_snapshot")
        if isinstance(tool_results.get("get_latest_live_crypto_edge_snapshot"), dict)
        else {}
    )
    crypto_edge_staleness = (
        tool_results.get("get_crypto_edge_staleness_summary")
        if isinstance(tool_results.get("get_crypto_edge_staleness_summary"), dict)
        else {}
    )
    crypto_edge_digest = (
        tool_results.get("get_crypto_edge_staleness_digest")
        if isinstance(tool_results.get("get_crypto_edge_staleness_digest"), dict)
        else {}
    )

    source_type = "fallback"
    source_family = "fallback"
    source_ids: list[str] = []
    source_name = "Fallback"
    source_names: list[str] = []
    freshness_label = "Missing"
    data_timestamp = None
    partial_provenance = True
    missing_provenance_reason = "Trusted evidence timestamps were unavailable."
    caveat_parts = ["Research only. Execution disabled."]

    if bool(latest_live_edges.get("has_live_data")):
        source_type = "live_public_structural"
        source_family = "live_public"
        source_ids = [
            "get_market_snapshot",
            "get_signal_summary",
            "get_latest_live_crypto_edge_snapshot",
        ]
        source_name = str(latest_live_edges.get("data_origin_label") or "Live Public")
        source_names = ["Market Snapshot", "Signal Summary", "Latest Live Crypto Edges"]
        freshness_label = str(latest_live_edges.get("freshness_summary") or "Unknown")
        live_timestamp = first_non_empty(
            (latest_live_edges.get("quote_meta") or {}).get("capture_ts"),
            (latest_live_edges.get("basis_meta") or {}).get("capture_ts"),
            (latest_live_edges.get("funding_meta") or {}).get("capture_ts"),
        )
        data_timestamp = first_non_empty(live_timestamp, market.get("as_of"))
        partial_provenance = not bool(live_timestamp)
        missing_provenance_reason = (
            None
            if live_timestamp
            else "Live-public structural snapshot timestamp was unavailable; market snapshot timestamp was used."
        )
    elif bool(crypto_edges.get("has_any_data")):
        source_type = "cached_research"
        source_family = "cached_research"
        source_ids = [
            "get_market_snapshot",
            "get_signal_summary",
            "get_crypto_edge_report",
        ]
        source_name = str(crypto_edges.get("data_origin_label") or "Cached Research")
        source_names = ["Market Snapshot", "Signal Summary", "Crypto Edge Report"]
        freshness_label = str(crypto_edges.get("freshness_summary") or "Unknown")
        structural_timestamp = first_non_empty(
            (crypto_edges.get("quote_meta") or {}).get("capture_ts"),
            (crypto_edges.get("basis_meta") or {}).get("capture_ts"),
            (crypto_edges.get("funding_meta") or {}).get("capture_ts"),
        )
        data_timestamp = first_non_empty(structural_timestamp, market.get("as_of"))
        missing_provenance_reason = (
            "Live-public structural snapshot was unavailable for this answer."
            if structural_timestamp
            else "Live-public structural snapshot was unavailable and cached structural timestamps were missing; market snapshot timestamp was used."
        )
        caveat_parts.append("No live-public structural snapshot was available for this answer.")
    elif str(market.get("as_of") or "").strip():
        source_type = "market_snapshot"
        source_family = "market_context"
        source_ids = ["get_market_snapshot", "get_signal_summary"]
        source_name = str(market.get("source") or market.get("exchange") or "Market Snapshot")
        source_names = ["Market Snapshot", "Signal Summary"]
        data_timestamp = str(market.get("as_of") or "")
        freshness_label = freshness_label_from_timestamp(data_timestamp)
        missing_provenance_reason = "Structural-edge snapshots were unavailable for this answer."
        caveat_parts.append("Structural-edge snapshots were unavailable for this answer.")
    else:
        caveat_parts.append("Trusted evidence timestamps were unavailable.")

    if bool(crypto_edge_staleness.get("needs_attention")):
        source_ids.append("get_crypto_edge_staleness_summary")
        source_names.append("Crypto Edge Staleness")
        caveat_parts.append(str(crypto_edge_staleness.get("summary_text") or "").strip())
    if str(crypto_edge_digest.get("while_away_summary") or "").strip():
        source_ids.append("get_crypto_edge_staleness_digest")
        source_names.append("Crypto Edge Digest")

    if not data_timestamp and missing_provenance_reason is None:
        partial_provenance = True
        missing_provenance_reason = "Trusted evidence timestamps were unavailable."

    freshness_status = freshness_status_from_label(freshness_label)
    age_seconds = timestamp_age_seconds(data_timestamp)
    source_ids = list(dict.fromkeys(item for item in source_ids if item))
    source_names = list(dict.fromkeys(item for item in source_names if item))

    metadata_status = "ok"
    if source_type == "fallback" or freshness_status == "missing":
        metadata_status = "critical"
    elif bool(crypto_edge_staleness.get("needs_attention")) or partial_provenance or freshness_status in {"aging", "stale"}:
        metadata_status = "warn"

    return AnswerMetadata(
        as_of=utc_now_iso(),
        source_type=source_type,
        source_family=source_family,
        source_ids=source_ids,
        freshness_status=freshness_status,
        age_seconds=age_seconds,
        confidence_label=confidence_label(confidence),
        caveat=" ".join(part for part in caveat_parts if part).strip() or None,
        partial_provenance=partial_provenance,
        missing_provenance_reason=missing_provenance_reason,
        source_name=source_name,
        source_names=source_names,
        data_timestamp=data_timestamp,
        metadata_status=metadata_status,
    ).model_dump()
