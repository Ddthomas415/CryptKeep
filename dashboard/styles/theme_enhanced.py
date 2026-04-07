from __future__ import annotations
import streamlit as st


def inject_enhanced_theme() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@400;600;700;800&display=swap');

:root {
  --ck-bg: #07111d;
  --ck-bg-soft: #0c1728;
  --ck-surface: rgba(15, 23, 38, 0.86);
  --ck-surface-strong: #121d31;
  --ck-border: rgba(117, 136, 173, 0.18);
  --ck-border-strong: rgba(117, 136, 173, 0.35);
  --ck-text: #edf3ff;
  --ck-muted: #8e9dbe;
  --ck-muted-strong: #a7b4d0;
  --ck-accent: #57a5ff;
  --ck-accent-soft: rgba(87, 165, 255, 0.14);
  --ck-success: #37d67a;
  --ck-warning: #f2b35d;
  --ck-danger: #ff6b7b;
  --ck-shadow: 0 24px 60px rgba(1, 7, 18, 0.45);
  --ck-glow: 0 0 24px rgba(87, 165, 255, 0.18);
  --ck-radius-lg: 22px;
  --ck-radius-md: 16px;
  --ck-radius-sm: 12px;
  --ck-font: "Sora", "SF Pro Display", "Avenir Next", sans-serif;
  --ck-mono: "IBM Plex Mono", "SF Mono", monospace;
}

html, body, [class*="css"] {
  font-family: var(--ck-font);
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(900px 400px at -10% -10%, rgba(87,165,255,0.12) 0%, transparent 60%),
    radial-gradient(700px 500px at 110% 0%, rgba(49,120,198,0.12) 0%, transparent 58%),
    linear-gradient(180deg, #08121e 0%, #091523 45%, #07111d 100%);
  color: var(--ck-text);
}

[data-testid="stSidebar"] {
  min-width: 260px; max-width: 260px;
  background: linear-gradient(180deg, rgba(9,14,26,0.99) 0%, rgba(7,11,21,0.98) 100%);
  border-right: 1px solid var(--ck-border);
}
[data-testid="stSidebar"] * { color: var(--ck-text); }
[data-testid="stSidebarNav"], [data-testid="stSidebarNavSeparator"] { display: none; }

[data-testid="stSidebar"] [data-testid="stPageLink"] a {
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  min-height: 2.8rem;
  padding: 0 0.75rem;
  display: flex; align-items: center;
  transition: all 150ms cubic-bezier(0.4,0,0.2,1);
  position: relative;
  overflow: hidden;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a::before {
  content: '';
  position: absolute; left: 0; top: 20%; bottom: 20%;
  width: 2px; border-radius: 2px;
  background: var(--ck-accent);
  opacity: 0;
  transition: opacity 150ms ease;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
  background: rgba(87,165,255,0.08);
  border-color: rgba(87,165,255,0.15);
  transform: translateX(3px);
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover::before { opacity: 1; }
[data-testid="stSidebar"] [data-testid="stPageLinkCurrent"] a,
[data-testid="stSidebar"] [data-testid="stPageLinkCurrent"] a:hover {
  background: linear-gradient(135deg, rgba(87,165,255,0.18) 0%, rgba(87,165,255,0.08) 100%);
  border-color: rgba(87,165,255,0.3);
  transform: translateX(3px);
}
[data-testid="stSidebar"] [data-testid="stPageLinkCurrent"] a::before { opacity: 1; }

div[data-testid="stVerticalBlockBorderWrapper"] {
  background: linear-gradient(180deg, var(--ck-surface) 0%, rgba(10,16,28,0.82) 100%);
  border: 1px solid var(--ck-border);
  border-radius: var(--ck-radius-lg);
  box-shadow: var(--ck-shadow);
  transition: border-color 200ms ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(117,136,173,0.28);
}

[data-testid="stButton"] > button,
.stDownloadButton > button {
  font-family: var(--ck-font);
  font-weight: 700;
  font-size: 0.875rem;
  letter-spacing: 0.01em;
  border-radius: 12px;
  border: 1px solid rgba(87,165,255,0.35);
  background: linear-gradient(180deg, rgba(87,165,255,0.22) 0%, rgba(87,165,255,0.12) 100%);
  color: #d8eaff;
  padding: 0.55rem 1.1rem;
  min-height: 2.5rem;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 160ms cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 1px 0 rgba(255,255,255,0.06) inset, 0 4px 12px rgba(87,165,255,0.08);
}
[data-testid="stButton"] > button::after,
.stDownloadButton > button::after {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, transparent 60%);
  pointer-events: none;
}
[data-testid="stButton"] > button:hover,
.stDownloadButton > button:hover {
  border-color: rgba(87,165,255,0.6);
  background: linear-gradient(180deg, rgba(87,165,255,0.32) 0%, rgba(87,165,255,0.2) 100%);
  color: #eef5ff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(87,165,255,0.2), 0 1px 0 rgba(255,255,255,0.08) inset;
}
[data-testid="stButton"] > button:active,
.stDownloadButton > button:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(87,165,255,0.12);
}
[data-testid="stButton"] > button[kind="primary"] {
  border-color: rgba(255,107,123,0.45);
  background: linear-gradient(180deg, rgba(255,107,123,0.88) 0%, rgba(228,70,88,0.84) 100%);
  color: #fff;
  box-shadow: 0 4px 16px rgba(255,107,123,0.22), 0 1px 0 rgba(255,255,255,0.1) inset;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
  border-color: rgba(255,107,123,0.7);
  background: linear-gradient(180deg, rgba(255,130,143,0.95) 0%, rgba(240,80,98,0.9) 100%);
  box-shadow: 0 8px 28px rgba(255,107,123,0.35), 0 1px 0 rgba(255,255,255,0.12) inset;
  transform: translateY(-2px);
}

.stTextInput input, .stTextArea textarea,
.stNumberInput input,
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
  font-family: var(--ck-font);
  background: rgba(8,14,26,0.95) !important;
  border: 1px solid rgba(117,136,173,0.25) !important;
  border-radius: 12px;
  color: var(--ck-text) !important;
  transition: border-color 150ms ease, box-shadow 150ms ease;
}
.stTextInput input:focus, .stTextArea textarea:focus,
[data-baseweb="input"]:focus-within > div {
  border-color: rgba(87,165,255,0.5) !important;
  box-shadow: 0 0 0 3px rgba(87,165,255,0.1) !important;
  outline: none;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
  color: rgba(142,157,190,0.5);
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 0.35rem;
  padding: 0.3rem;
  background: rgba(8,14,26,0.6);
  border-radius: 14px;
  border: 1px solid var(--ck-border);
  width: fit-content;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--ck-muted);
  padding: 0.45rem 1rem;
  font-weight: 600;
  font-size: 0.84rem;
  transition: all 150ms ease;
  cursor: pointer;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
  background: rgba(87,165,255,0.08);
  color: var(--ck-muted-strong);
}
[data-testid="stTabs"] [aria-selected="true"] {
  background: linear-gradient(180deg, rgba(87,165,255,0.2) 0%, rgba(87,165,255,0.12) 100%);
  border-color: rgba(87,165,255,0.3);
  color: #d8eaff;
  box-shadow: 0 2px 8px rgba(87,165,255,0.12);
}

[data-testid="stMetric"] {
  background: linear-gradient(180deg, rgba(14,22,38,0.9) 0%, rgba(9,15,26,0.85) 100%);
  border: 1px solid var(--ck-border);
  border-radius: var(--ck-radius-md);
  padding: 1rem 1.1rem;
  transition: border-color 150ms ease, transform 150ms ease;
}
[data-testid="stMetric"]:hover {
  border-color: rgba(87,165,255,0.28);
  transform: translateY(-1px);
}
[data-testid="stMetricLabel"] {
  font-size: 0.72rem !important;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--ck-muted) !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.85rem !important;
  font-weight: 800 !important;
  letter-spacing: -0.04em;
  color: var(--ck-text) !important;
}
[data-testid="stMetricDelta"] { color: var(--ck-muted-strong) !important; }

[data-testid="stInfo"] {
  background: rgba(87,165,255,0.07);
  border: 1px solid rgba(87,165,255,0.22);
  border-left: 3px solid var(--ck-accent);
  border-radius: 12px;
}
[data-testid="stSuccess"] {
  background: rgba(55,214,122,0.07);
  border: 1px solid rgba(55,214,122,0.22);
  border-left: 3px solid var(--ck-success);
  border-radius: 12px;
}
[data-testid="stWarning"] {
  background: rgba(242,179,93,0.08);
  border: 1px solid rgba(242,179,93,0.24);
  border-left: 3px solid var(--ck-warning);
  border-radius: 12px;
}
[data-testid="stError"] {
  background: rgba(255,107,123,0.08);
  border: 1px solid rgba(255,107,123,0.26);
  border-left: 3px solid var(--ck-danger);
  border-radius: 12px;
}

[data-testid="stCodeBlock"] pre,
[data-testid="stCode"] pre,
code {
  font-family: var(--ck-mono) !important;
  background: #06101c !important;
  border: 1px solid var(--ck-border);
  border-radius: 12px;
}

[data-testid="stSpinner"] { color: var(--ck-accent); }

[data-baseweb="checkbox"] [data-checked] {
  background: var(--ck-accent);
  border-color: var(--ck-accent);
}

[data-baseweb="select"] [data-testid="stSelectboxLabel"],
[data-testid="stSelectbox"] label {
  font-size: 0.78rem;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--ck-muted);
}

h1 { font-size: 2.2rem; line-height: 1.05; letter-spacing: -0.05em; font-weight: 800; }
h2 { font-size: 1.55rem; line-height: 1.15; letter-spacing: -0.03em; font-weight: 700; }
h3 { font-size: 1.05rem; line-height: 1.25; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 0.75rem; }

[data-testid="stExpander"] {
  border: 1px solid var(--ck-border) !important;
  border-radius: 14px !important;
  background: rgba(10,16,28,0.7) !important;
  transition: border-color 150ms ease;
}
[data-testid="stExpander"]:hover {
  border-color: rgba(87,165,255,0.25) !important;
}
[data-testid="stExpander"] summary {
  cursor: pointer;
  font-weight: 600;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(117,136,173,0.25);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(117,136,173,0.4); }

[data-testid="stDataFrame"] {
  border-radius: var(--ck-radius-md);
  border: 1px solid var(--ck-border);
  overflow: hidden;
}
[data-testid="stDataFrame"] [role="columnheader"] {
  background: rgba(87,165,255,0.08) !important;
  color: var(--ck-muted-strong) !important;
  font-weight: 700;
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.ai-copilot-response {
  font-family: var(--ck-font);
  line-height: 1.7;
  color: var(--ck-muted-strong);
}
.ai-copilot-response strong {
  color: var(--ck-text);
  font-weight: 700;
}

[data-testid="stCaptionContainer"] p,
small, .caption {
  font-family: var(--ck-mono);
  font-size: 0.75rem;
  color: var(--ck-muted);
}

hr, [data-testid="stDivider"] {
  border-color: rgba(117,136,173,0.1);
}

/* ── FIX: Sign in button needs high contrast ── */
[data-testid="stForm"] [data-testid="stButton"] > button,
[data-testid="stForm"] button[type="submit"],
form [data-testid="stButton"] > button {
  background: linear-gradient(180deg, #57a5ff 0%, #3d8fe8 100%) !important;
  border-color: rgba(87,165,255,0.8) !important;
  color: #fff !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 16px rgba(87,165,255,0.35) !important;
  min-width: 100px;
}
[data-testid="stForm"] [data-testid="stButton"] > button:hover {
  background: linear-gradient(180deg, #6db3ff 0%, #4d9ef5 100%) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(87,165,255,0.45) !important;
}

/* ── FIX: Mono font only for code/captions, not body text ── */
[data-testid="stCaptionContainer"] p,
small, .caption,
[data-testid="stCodeBlock"] pre,
[data-testid="stCode"] pre,
code {
  font-family: var(--ck-mono) !important;
}

/* Body text and headings stay on Sora */
[data-testid="stMarkdownContainer"] p,
[data-testid="stText"],
[data-testid="stButton"] > button,
label, .stSelectbox label,
[data-baseweb="select"] {
  font-family: var(--ck-font) !important;
}



/* Exact Streamlit login submit button selector */
button[data-testid="stBaseButton-secondaryFormSubmit"][kind="secondaryFormSubmit"] {
  background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%) !important;
  border: 1px solid #dc2626 !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.10), 0 2px 4px -2px rgba(0,0,0,0.10) !important;
  transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease !important;
}

button[data-testid="stBaseButton-secondaryFormSubmit"][kind="secondaryFormSubmit"]:hover,
button[data-testid="stBaseButton-secondaryFormSubmit"][kind="secondaryFormSubmit"]:focus-visible {
  background: linear-gradient(180deg, #dc2626 0%, #b91c1c 100%) !important;
  border-color: #991b1b !important;
  color: #ffffff !important;
  box-shadow: 0 8px 16px rgba(220,38,38,0.28) !important;
}

button[data-testid="stBaseButton-secondaryFormSubmit"][kind="secondaryFormSubmit"]:disabled {
  opacity: 0.65 !important;
}

</style>
""", unsafe_allow_html=True)
