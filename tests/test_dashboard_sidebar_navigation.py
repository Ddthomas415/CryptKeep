from __future__ import annotations

from pathlib import Path

from dashboard.components.sidebar import DEFAULT_NAV_ITEMS


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_NAV_ITEMS = (
    ("app.py", "Overview", "🏠"),
    ("pages/10_Markets.py", "Markets", "📈"),
    ("pages/20_Portfolio.py", "Portfolio", "💼"),
    ("pages/30_Signals.py", "Signals", "🧠"),
    ("pages/35_Research.py", "Research", "🔬"),
    ("pages/40_Trades.py", "Trades", "🔁"),
    ("pages/50_Automation.py", "Automation", "⚙️"),
    ("pages/60_Operations.py", "Operations", "🛠️"),
    ("pages/70_Settings.py", "Settings", "🔒"),
)

SIDEBAR_ENABLED_FILES = (
    "dashboard/app.py",
    "dashboard/pages/00_Operator.py",
    "dashboard/pages/10_Markets.py",
    "dashboard/pages/20_Portfolio.py",
    "dashboard/pages/30_Signals.py",
    "dashboard/pages/35_Research.py",
    "dashboard/pages/40_Trades.py",
    "dashboard/pages/50_Automation.py",
    "dashboard/pages/60_Operations.py",
    "dashboard/pages/70_Settings.py",
    "dashboard/pages/99_Legacy_UI.py",
)

AUTH_ROLE_REQUIREMENTS = {
    "dashboard/app.py": "VIEWER",
    "dashboard/pages/10_Markets.py": "VIEWER",
    "dashboard/pages/20_Portfolio.py": "VIEWER",
    "dashboard/pages/30_Signals.py": "VIEWER",
    "dashboard/pages/35_Research.py": "VIEWER",
    "dashboard/pages/40_Trades.py": "VIEWER",
    "dashboard/pages/50_Automation.py": "VIEWER",
    "dashboard/pages/60_Operations.py": "OPERATOR",
    "dashboard/pages/70_Settings.py": "VIEWER",
    "dashboard/pages/00_Operator.py": "OPERATOR",
    "dashboard/pages/99_Legacy_UI.py": "OPERATOR",
}


def test_default_nav_items_contract() -> None:
    assert DEFAULT_NAV_ITEMS == EXPECTED_NAV_ITEMS


def test_sidebar_rendered_across_dashboard_pages() -> None:
    for relative_path in SIDEBAR_ENABLED_FILES:
        file_path = REPO_ROOT / relative_path
        assert file_path.exists(), f"Missing dashboard file: {relative_path}"
        source = file_path.read_text(encoding="utf-8")
        assert "render_app_sidebar(" in source, f"Shared sidebar not wired in {relative_path}"


def test_auth_gating_consistent_across_dashboard_pages() -> None:
    for relative_path, required_role in AUTH_ROLE_REQUIREMENTS.items():
        file_path = REPO_ROOT / relative_path
        assert file_path.exists(), f"Missing dashboard file: {relative_path}"
        source = file_path.read_text(encoding="utf-8")
        expected = f'require_authenticated_role("{required_role}")'
        assert expected in source, f"Auth gate mismatch in {relative_path}"


def test_legacy_ui_page_is_retired_stub() -> None:
    file_path = REPO_ROOT / "dashboard/pages/99_Legacy_UI.py"
    source = file_path.read_text(encoding="utf-8")
    assert "Legacy UI (Retired)" in source
    assert "importlib.util" not in source
    assert "CBP_ENABLE_LEGACY_UI" not in source
