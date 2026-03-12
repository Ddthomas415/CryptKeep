from __future__ import annotations

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --ck-bg: #07111d;
          --ck-bg-soft: #0c1728;
          --ck-surface: rgba(15, 23, 38, 0.86);
          --ck-surface-strong: #121d31;
          --ck-surface-muted: rgba(13, 20, 34, 0.72);
          --ck-border: rgba(117, 136, 173, 0.18);
          --ck-border-strong: rgba(117, 136, 173, 0.3);
          --ck-text: #edf3ff;
          --ck-muted: #8e9dbe;
          --ck-muted-strong: #a7b4d0;
          --ck-accent: #57a5ff;
          --ck-accent-soft: rgba(87, 165, 255, 0.14);
          --ck-success: #37d67a;
          --ck-warning: #f2b35d;
          --ck-danger: #ff6b7b;
          --ck-shadow: 0 24px 60px rgba(1, 7, 18, 0.35);
          --ck-radius-lg: 22px;
          --ck-radius-md: 16px;
          --ck-radius-sm: 12px;
          --ck-font: "SF Pro Display", "Avenir Next", "Segoe UI", sans-serif;
        }
        html, body, [class*="css"]  {
          font-family: var(--ck-font);
        }
        [data-testid="stAppViewContainer"] {
          background:
            radial-gradient(900px 400px at -10% -10%, rgba(87, 165, 255, 0.14) 0%, transparent 60%),
            radial-gradient(700px 500px at 110% 0%, rgba(49, 120, 198, 0.14) 0%, transparent 58%),
            linear-gradient(180deg, #08121e 0%, #091523 45%, #07111d 100%);
          color: var(--ck-text);
        }
        [data-testid="stHeader"] {
          background: rgba(7, 17, 29, 0.75);
          border-bottom: 1px solid rgba(117, 136, 173, 0.08);
          backdrop-filter: blur(12px);
        }
        [data-testid="stToolbar"] {
          right: 1rem;
        }
        [data-testid="stAppViewContainer"] > .main .block-container {
          max-width: 1500px;
          padding-top: 1.4rem;
          padding-bottom: 3rem;
          padding-left: 2rem;
          padding-right: 2rem;
        }
        [data-testid="stSidebar"] {
          min-width: 280px;
          max-width: 280px;
          background:
            linear-gradient(180deg, rgba(13, 20, 34, 0.98) 0%, rgba(9, 15, 27, 0.97) 100%);
          border-right: 1px solid var(--ck-border);
          box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.03);
        }
        [data-testid="stSidebar"] * {
          color: var(--ck-text);
        }
        [data-testid="stSidebar"] .block-container {
          padding-top: 1.2rem;
          padding-left: 1rem;
          padding-right: 1rem;
        }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"] {
          color: var(--ck-muted);
        }
        h1, h2, h3 {
          color: var(--ck-text);
          letter-spacing: -0.03em;
        }
        h1 {
          font-size: 2.3rem;
          line-height: 1.05;
          margin-bottom: 0.25rem;
        }
        h2 {
          font-size: 1.6rem;
          line-height: 1.15;
        }
        h3 {
          font-size: 1.05rem;
          line-height: 1.25;
          margin-bottom: 0.8rem;
        }
        a {
          color: inherit;
          text-decoration: none;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"] {
          margin-bottom: 0.2rem;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
          border: 1px solid transparent;
          border-radius: 14px;
          background: transparent;
          min-height: 2.7rem;
          transition: background 120ms ease, border-color 120ms ease, transform 120ms ease;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
          background: rgba(87, 165, 255, 0.09);
          border-color: rgba(87, 165, 255, 0.18);
          transform: translateX(2px);
        }
        [data-testid="stSidebar"] [data-testid="stPageLinkCurrent"] a,
        [data-testid="stSidebar"] [data-testid="stPageLinkCurrent"] a:hover {
          background: linear-gradient(180deg, rgba(87, 165, 255, 0.2) 0%, rgba(87, 165, 255, 0.14) 100%);
          border-color: rgba(87, 165, 255, 0.34);
          box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
          background: linear-gradient(180deg, var(--ck-surface) 0%, var(--ck-surface-muted) 100%);
          border: 1px solid var(--ck-border);
          border-radius: var(--ck-radius-lg);
          box-shadow: var(--ck-shadow);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
          border-radius: var(--ck-radius-lg);
        }
        [data-testid="column"] div[data-testid="stVerticalBlockBorderWrapper"] {
          min-height: 100%;
        }
        [data-testid="stButton"] > button,
        .stDownloadButton > button {
          border-radius: 14px;
          border: 1px solid rgba(87, 165, 255, 0.22);
          background: linear-gradient(180deg, rgba(87, 165, 255, 0.18) 0%, rgba(87, 165, 255, 0.1) 100%);
          color: var(--ck-text);
          font-weight: 600;
          box-shadow: none;
          transition: transform 120ms ease, border-color 120ms ease, background 120ms ease;
        }
        [data-testid="stButton"] > button:hover,
        .stDownloadButton > button:hover {
          border-color: rgba(87, 165, 255, 0.4);
          background: linear-gradient(180deg, rgba(87, 165, 255, 0.24) 0%, rgba(87, 165, 255, 0.16) 100%);
          transform: translateY(-1px);
        }
        [data-testid="stButton"] > button[kind="primary"],
        .st-emotion-cache-1vt4y43 button[kind="primary"] {
          border-color: rgba(255, 107, 123, 0.28);
          background: linear-gradient(180deg, rgba(255, 107, 123, 0.92) 0%, rgba(244, 86, 102, 0.88) 100%);
          color: white;
        }
        [data-testid="stButton"] > button[kind="primary"]:hover {
          border-color: rgba(255, 107, 123, 0.48);
          background: linear-gradient(180deg, rgba(255, 123, 136, 0.96) 0%, rgba(244, 86, 102, 0.92) 100%);
        }
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div {
          background: rgba(11, 18, 32, 0.92);
          border: 1px solid var(--ck-border);
          border-radius: 14px;
          color: var(--ck-text);
        }
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
          color: var(--ck-muted);
        }
        [data-baseweb="select"] svg,
        [data-baseweb="select"] * {
          color: var(--ck-text);
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
          gap: 0.45rem;
          padding-bottom: 0.2rem;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
          border-radius: 999px;
          border: 1px solid transparent;
          background: rgba(87, 165, 255, 0.05);
          color: var(--ck-muted-strong);
          padding: 0.4rem 0.95rem;
        }
        [data-testid="stTabs"] [aria-selected="true"] {
          background: rgba(87, 165, 255, 0.18);
          border-color: rgba(87, 165, 255, 0.28);
          color: var(--ck-text);
        }
        [data-testid="stDataFrame"] {
          border-radius: var(--ck-radius-md);
          overflow: hidden;
          border: 1px solid var(--ck-border);
          background: rgba(8, 14, 24, 0.72);
        }
        [data-testid="stDataFrame"] [role="grid"] {
          background: rgba(8, 14, 24, 0.78);
        }
        [data-testid="stDataFrame"] [role="columnheader"] {
          background: rgba(87, 165, 255, 0.08);
          color: var(--ck-muted-strong);
          font-weight: 600;
        }
        [data-testid="stDataFrame"] [role="gridcell"] {
          color: var(--ck-text);
        }
        [data-testid="stInfo"] {
          background: rgba(87, 165, 255, 0.08);
          border: 1px solid rgba(87, 165, 255, 0.18);
          color: var(--ck-muted-strong);
          border-radius: 16px;
        }
        [data-testid="stSuccess"] {
          background: rgba(55, 214, 122, 0.08);
          border: 1px solid rgba(55, 214, 122, 0.2);
          border-radius: 16px;
        }
        [data-testid="stWarning"] {
          background: rgba(242, 179, 93, 0.08);
          border: 1px solid rgba(242, 179, 93, 0.2);
          border-radius: 16px;
        }
        [data-testid="stError"] {
          background: rgba(255, 107, 123, 0.1);
          border: 1px solid rgba(255, 107, 123, 0.22);
          border-radius: 16px;
        }
        [data-testid="stCodeBlock"] pre,
        [data-testid="stCode"] pre {
          background: #06101c;
          border: 1px solid var(--ck-border);
          border-radius: 16px;
        }
        hr, [data-testid="stDivider"] {
          border-color: rgba(117, 136, 173, 0.1);
        }
        .ck-page-intro {
          padding: 0.2rem 0 0.8rem 0;
        }
        .ck-page-intro p {
          margin: 0.3rem 0 0;
          max-width: 54rem;
          font-size: 0.96rem;
          color: var(--ck-muted);
        }
        .ck-badge-row {
          display: flex;
          justify-content: flex-end;
          flex-wrap: wrap;
          gap: 0.55rem;
          padding-top: 0.4rem;
        }
        .ck-badge {
          display: inline-flex;
          flex-direction: column;
          min-width: 8.4rem;
          border-radius: 16px;
          border: 1px solid var(--ck-border);
          background: rgba(10, 17, 30, 0.78);
          padding: 0.7rem 0.85rem;
          text-align: left;
        }
        .ck-badge-label {
          font-size: 0.68rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--ck-muted);
        }
        .ck-badge-value {
          font-size: 0.94rem;
          font-weight: 600;
          color: var(--ck-text);
          margin-top: 0.18rem;
        }
        .ck-brand {
          border: 1px solid var(--ck-border);
          border-radius: 20px;
          background: linear-gradient(180deg, rgba(14, 23, 37, 0.94) 0%, rgba(10, 16, 28, 0.94) 100%);
          padding: 1.05rem 1rem;
          margin-bottom: 1rem;
          box-shadow: var(--ck-shadow);
        }
        .ck-brand-title {
          font-size: 1.4rem;
          line-height: 1.1;
          font-weight: 700;
          color: var(--ck-text);
          letter-spacing: -0.03em;
        }
        .ck-brand-subtitle {
          margin-top: 0.25rem;
          font-size: 0.92rem;
          color: var(--ck-muted);
        }
        .ck-brand-pills {
          display: flex;
          flex-wrap: wrap;
          gap: 0.45rem;
          margin-top: 0.85rem;
        }
        .ck-brand-pill {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          border: 1px solid rgba(87, 165, 255, 0.2);
          background: rgba(87, 165, 255, 0.08);
          color: var(--ck-muted-strong);
          font-size: 0.76rem;
          padding: 0.26rem 0.62rem;
        }
        .ck-nav-label {
          margin: 0.9rem 0 0.45rem;
          font-size: 0.72rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--ck-muted);
        }
        .ck-kpi-card {
          padding: 1.2rem 1.15rem 1.05rem;
          min-height: 8.6rem;
        }
        .ck-kpi-label {
          font-size: 0.75rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--ck-muted);
          margin-bottom: 0.85rem;
        }
        .ck-kpi-value {
          font-size: 2rem;
          line-height: 1;
          font-weight: 700;
          letter-spacing: -0.04em;
          color: var(--ck-text);
        }
        .ck-kpi-delta {
          margin-top: 0.8rem;
          color: var(--ck-muted-strong);
          font-size: 0.9rem;
        }
        .ck-section-head {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 1rem;
          margin-bottom: 0.75rem;
        }
        .ck-section-title {
          margin: 0;
          font-size: 1.08rem;
          font-weight: 650;
          color: var(--ck-text);
          letter-spacing: -0.02em;
        }
        .ck-section-meta {
          color: var(--ck-muted);
          font-size: 0.8rem;
          white-space: nowrap;
        }
        .ck-activity-list {
          display: flex;
          flex-direction: column;
          gap: 0.7rem;
        }
        .ck-activity-item {
          border: 1px solid var(--ck-border);
          background: rgba(9, 15, 27, 0.74);
          border-radius: 14px;
          padding: 0.85rem 0.95rem;
          color: var(--ck-muted-strong);
          font-size: 0.92rem;
        }
        .ck-log-shell {
          display: flex;
          flex-direction: column;
          gap: 0.35rem;
        }
        .ck-log-meta {
          color: var(--ck-muted);
          font-size: 0.84rem;
        }
        .ck-sidebar-note {
          border: 1px solid var(--ck-border);
          border-radius: 16px;
          background: rgba(10, 17, 30, 0.76);
          padding: 0.9rem 1rem;
          margin-top: 1rem;
          color: var(--ck-muted);
          font-size: 0.86rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
