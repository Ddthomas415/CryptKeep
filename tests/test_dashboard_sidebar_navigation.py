from __future__ import annotations

from pathlib import Path

from dashboard.components import sidebar as sidebar_component
from dashboard.components.sidebar import DEFAULT_BRAND_PILLS, DEFAULT_NAV_ITEMS, OPERATOR_NAV_ITEMS


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_NAV_ITEMS = (
    ("pages/00_Home.py", "Home", "🏠"),
    ("pages/05_Help.py", "Help", "❓"),
    ("app.py", "Overview", "📋"),
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
    "dashboard/pages/00_Home.py",
    "dashboard/pages/05_Help.py",
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
    "dashboard/pages/00_Home.py": "VIEWER",
    "dashboard/pages/05_Help.py": "VIEWER",
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


def test_default_brand_pills_are_neutral() -> None:
    assert DEFAULT_BRAND_PILLS == ("Role Gated", "Workflow Shell")


def test_operator_secondary_nav_items_contract() -> None:
    assert OPERATOR_NAV_ITEMS == (
        ("pages/65_Copilot_Reports.py", "Copilot Reports", "🤖"),
        ("pages/00_Operator.py", "Operator (Legacy)", "↩️"),
        ("pages/99_Legacy_UI.py", "Legacy UI", "🗃️"),
    )


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


def test_render_app_sidebar_renders_neutral_default_pills(monkeypatch) -> None:
    calls: list[str] = []

    class _SidebarCtx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _FakeStreamlit:
        def __init__(self) -> None:
            self.sidebar = _SidebarCtx()
            self.session_state: dict[str, object] = {}

        def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
            calls.append(str(text))

        def page_link(self, path: str, *, label: str, icon: str) -> None:
            calls.append(f"{path}|{label}|{icon}")

    monkeypatch.setattr(sidebar_component, "st", _FakeStreamlit())

    sidebar_component.render_app_sidebar()

    rendered = "\n".join(calls)
    assert "Research Only" not in rendered
    assert "Paper Safe" not in rendered
    assert "Role Gated" in rendered
    assert "Workflow Shell" in rendered


def test_render_app_sidebar_hides_operator_secondary_nav_for_viewers(monkeypatch) -> None:
    calls: list[str] = []

    class _SidebarCtx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _FakeStreamlit:
        def __init__(self) -> None:
            self.sidebar = _SidebarCtx()
            self.session_state = {"cbp_auth_session": {"role": "VIEWER"}}

        def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
            calls.append(str(text))

        def page_link(self, path: str, *, label: str, icon: str) -> None:
            calls.append(f"{path}|{label}|{icon}")

    monkeypatch.setattr(sidebar_component, "st", _FakeStreamlit())

    sidebar_component.render_app_sidebar()

    rendered = "\n".join(calls)
    assert "Copilot Reports" not in rendered
    assert "Operator (Legacy)" not in rendered
    assert "Legacy UI" not in rendered


def test_render_app_sidebar_adds_operator_secondary_nav_for_operator_role(monkeypatch) -> None:
    calls: list[str] = []

    class _SidebarCtx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _FakeStreamlit:
        def __init__(self) -> None:
            self.sidebar = _SidebarCtx()
            self.session_state = {"cbp_auth_session": {"role": "OPERATOR"}}

        def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
            calls.append(str(text))

        def page_link(self, path: str, *, label: str, icon: str) -> None:
            calls.append(f"{path}|{label}|{icon}")

    monkeypatch.setattr(sidebar_component, "st", _FakeStreamlit())

    sidebar_component.render_app_sidebar()

    rendered = "\n".join(calls)
    assert "Operator / Reports" in rendered
    assert "pages/65_Copilot_Reports.py|Copilot Reports|🤖" in rendered
    assert "pages/00_Operator.py|Operator (Legacy)|↩️" in rendered
    assert "pages/99_Legacy_UI.py|Legacy UI|🗃️" in rendered
