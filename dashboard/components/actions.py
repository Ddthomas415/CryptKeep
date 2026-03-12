from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

SystemAction = tuple[str, list[str]]

PRIMARY_ACTIONS: tuple[SystemAction, ...] = (
    ("Preflight", ["preflight"]),
    ("Status All", ["status-all"]),
    ("Diagnostic", ["diag", "--lines", "80"]),
    ("Clean Locks", ["clean"]),
)

SECONDARY_ACTIONS: tuple[SystemAction, ...] = (
    ("Start All", ["start-all"]),
    ("Stop All", ["stop-all"]),
)


def _render_action_row(
    actions: Sequence[SystemAction],
    *,
    key_prefix: str,
    columns: int,
) -> SystemAction | None:
    cols = st.columns(columns)
    for idx, (label, args) in enumerate(actions):
        with cols[idx]:
            if st.button(label, width="stretch", key=f"{key_prefix}_{idx}"):
                return label, list(args)
    return None


def render_system_action_buttons(*, key_prefix: str = "ops_system") -> SystemAction | None:
    action = _render_action_row(PRIMARY_ACTIONS, key_prefix=f"{key_prefix}_primary", columns=4)
    if action:
        return action
    return _render_action_row(SECONDARY_ACTIONS, key_prefix=f"{key_prefix}_secondary", columns=2)
