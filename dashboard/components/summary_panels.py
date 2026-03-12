from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st


def resolve_asset_row(
    rows: Sequence[dict[str, Any]] | None,
    *,
    asset: str,
    asset_field: str = "asset",
) -> dict[str, Any]:
    target = str(asset or "")
    return next(
        (
            item
            for item in rows or []
            if isinstance(item, dict) and str(item.get(asset_field) or "") == target
        ),
        {},
    )


def render_market_context(detail: dict[str, Any] | None) -> None:
    payload = detail if isinstance(detail, dict) else {}
    with st.container(border=True):
        st.markdown("### Market Context")
        st.caption(f"Support: ${float(payload.get('support') or 0.0):,.2f}")
        st.caption(f"Resistance: ${float(payload.get('resistance') or 0.0):,.2f}")
        st.caption(f"Evidence: {str(payload.get('evidence') or 'No evidence available.')}")


def render_signal_thesis(
    rows: Sequence[dict[str, Any]] | None,
    detail: dict[str, Any] | None,
    *,
    fallback_asset: str,
) -> None:
    payload = detail if isinstance(detail, dict) else {}
    selected_row = resolve_asset_row(rows, asset=str(payload.get("asset") or fallback_asset))

    with st.container(border=True):
        st.markdown("### Signal Thesis")
        st.caption(
            str(selected_row.get("summary") or payload.get("current_cause") or "No signal thesis available.")
        )
        st.caption(
            f"Evidence: {str(selected_row.get('evidence') or payload.get('evidence') or 'No evidence available.')}"
        )
