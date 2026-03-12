from __future__ import annotations

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ck-bg: #0b1020;
          --ck-surface: #11182d;
          --ck-border: #29324d;
          --ck-text: #e5ecff;
          --ck-muted: #96a3c7;
          --ck-accent: #4f8cff;
        }
        [data-testid="stAppViewContainer"] {
          background: radial-gradient(1400px 500px at 10% -10%, #1a2744 0%, var(--ck-bg) 45%);
          color: var(--ck-text);
        }
        [data-testid="stSidebar"] {
          background: #0d1427;
          border-right: 1px solid var(--ck-border);
        }
        [data-testid="stSidebar"] * {
          color: var(--ck-text);
        }
        [data-testid="stMarkdownContainer"] p {
          color: var(--ck-muted);
        }
        [data-testid="stMetricValue"] {
          color: var(--ck-text);
        }
        [data-testid="stMetricDelta"] {
          color: #37d67a;
        }
        div[data-testid="stVerticalBlock"] div[data-testid="stContainer"] {
          background: color-mix(in srgb, var(--ck-surface) 90%, transparent);
          border: 1px solid var(--ck-border);
          border-radius: 14px;
          padding: 0.5rem 0.75rem;
        }
        .ck-badge {
          display: inline-block;
          border: 1px solid var(--ck-border);
          border-radius: 999px;
          background: color-mix(in srgb, var(--ck-accent) 20%, transparent);
          color: #cfe0ff;
          font-size: 12px;
          padding: 0.2rem 0.65rem;
          margin: 0.15rem 0 0.25rem 0.35rem;
          float: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
