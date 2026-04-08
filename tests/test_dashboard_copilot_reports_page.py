from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class _DummyBlock:
    def __enter__(self) -> "_DummyBlock":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def __getattr__(self, _name: str):
        return lambda *args, **kwargs: None


class _FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.sidebar = _DummyBlock()
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.successes: list[str] = []
        self.infos: list[str] = []
        self.writes: list[object] = []

    def __getattr__(self, _name: str):
        return lambda *args, **kwargs: None

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [_DummyBlock() for _ in range(count)]

    def tabs(self, labels):
        return [_DummyBlock() for _ in labels]

    def container(self, *args, **kwargs):
        return _DummyBlock()

    def expander(self, *args, **kwargs):
        return _DummyBlock()

    def selectbox(self, label, options, index=0, **kwargs):
        values = list(options)
        return values[index] if values else None

    def warning(self, message):
        self.warnings.append(str(message))

    def error(self, message):
        self.errors.append(str(message))

    def success(self, message):
        self.successes.append(str(message))

    def info(self, message):
        self.infos.append(str(message))

    def write(self, value):
        self.writes.append(value)


def test_copilot_reports_page_imports(monkeypatch) -> None:
    fake_streamlit = _FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    from dashboard import auth_gate
    from dashboard.components import header, sidebar, cards
    from dashboard.services import copilot_reports

    monkeypatch.setattr(auth_gate, "require_authenticated_role", lambda required_role="OPERATOR": {"ok": True, "role": required_role})
    monkeypatch.setattr(sidebar, "render_app_sidebar", lambda *args, **kwargs: None)
    monkeypatch.setattr(header, "render_page_header", lambda *args, **kwargs: None)
    monkeypatch.setattr(cards, "render_feature_hero", lambda *args, **kwargs: None)
    monkeypatch.setattr(cards, "render_prompt_actions", lambda *args, **kwargs: None)
    monkeypatch.setattr(cards, "render_section_intro", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        copilot_reports,
        "summarize_copilot_reports",
        lambda limit=50: {
            "report_count": 2,
            "kind_counts": {"repo_review": 1, "strategy_lab": 1},
            "severity_counts": {"ok": 1, "warn": 1},
            "latest_kind": "strategy_lab",
            "latest_generated_at": "2026-04-08T00:00:00+00:00",
        },
    )
    monkeypatch.setattr(
        copilot_reports,
        "list_copilot_reports",
        lambda limit=30: [
            {
                "stem": "strategy_lab_smoke",
                "kind": "strategy_lab",
                "severity": "warn",
                "generated_at": "2026-04-08T00:00:00+00:00",
            }
        ],
    )
    monkeypatch.setattr(
        copilot_reports,
        "load_copilot_report_bundle",
        lambda stem: {
            "payload": {
                "summary": "Strategy lab summary.",
                "collector_runtime": {
                    "status": "stopped",
                    "completed_strategies": 1,
                    "total_strategies": 3,
                    "summary_text": "Paper evidence collector is stopped (1/3 complete).",
                },
            },
            "markdown": "# Strategy Lab\n",
        },
    )

    path = REPO_ROOT / "dashboard/pages/65_Copilot_Reports.py"
    spec = importlib.util.spec_from_file_location("dashboard.pages.copilot_reports", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert any("partial evidence" in msg.lower() or "1/3 complete" in msg.lower() for msg in fake_streamlit.warnings)
    assert any(isinstance(item, dict) and item.get("completed_strategies") == 1 for item in fake_streamlit.writes)
