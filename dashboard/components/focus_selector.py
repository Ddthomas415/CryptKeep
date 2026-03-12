from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st


def resolve_focus_options(
    rows: Sequence[dict[str, Any]] | None,
    *,
    selected_asset: str | None = None,
    fallback_asset: str = "SOL",
    asset_field: str = "asset",
) -> tuple[list[str], str]:
    options = [
        str(item.get(asset_field) or "")
        for item in rows or []
        if isinstance(item, dict) and str(item.get(asset_field) or "").strip()
    ]
    default_asset = str(selected_asset or (options[0] if options else fallback_asset))
    if options and default_asset not in options:
        default_asset = options[0]
    return options, default_asset


def render_focus_selector(
    rows: Sequence[dict[str, Any]] | None,
    *,
    label: str,
    selected_asset: str | None = None,
    fallback_asset: str = "SOL",
    asset_field: str = "asset",
    key: str,
) -> tuple[str, str, list[str]]:
    options, default_asset = resolve_focus_options(
        rows,
        selected_asset=selected_asset,
        fallback_asset=fallback_asset,
        asset_field=asset_field,
    )
    choice = st.selectbox(
        label,
        options or [default_asset],
        index=(options.index(default_asset) if default_asset in options else 0),
        key=key,
    )
    return str(choice), default_asset, options
