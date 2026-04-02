from __future__ import annotations

import asyncio

from services.admin import preflight as ap
from services.os.ports import PortResolution



def test_run_preflight_accepts_extended_signature_without_private_checks(monkeypatch):
    monkeypatch.setattr(ap, "ensure_kill_default", lambda: None)
    monkeypatch.setattr(ap, "kill_state", lambda: {"armed": True, "note": "default"})

    out = asyncio.run(
        ap.run_preflight(
            venues=["Coinbase"],
            symbols=["ETH/USD"],
            time_tolerance_ms=999,
            do_private_check=False,
        )
    )

    assert out["ok"] is True
    assert out["venues"] == ["coinbase"]
    assert out["symbols"] == ["ETH/USD"]
    assert out["time_tolerance_ms"] == 999
    assert out["private_checks_enabled"] is False
    assert out["private_connectivity"] == []
    assert out["permission_probes"] == []
    assert out["probe_keys"] == list(ap.DEFAULT_PROBES)



def test_run_preflight_collects_private_connectivity_and_probe_results(monkeypatch):
    monkeypatch.setattr(ap, "ensure_kill_default", lambda: None)
    monkeypatch.setattr(ap, "kill_state", lambda: {"armed": True, "note": "default"})
    monkeypatch.setattr(
        ap,
        "test_private_connectivity",
        lambda exchange, sandbox=False: {"ok": exchange == "coinbase", "exchange": exchange, "sandbox": bool(sandbox)},
    )
    monkeypatch.setattr(
        ap,
        "run_probes",
        lambda exchange, probe_keys, sandbox=False: {
            "ok": True,
            "exchange": exchange,
            "sandbox": bool(sandbox),
            "results": [{"probe": p} for p in probe_keys],
        },
    )

    out = asyncio.run(
        ap.run_preflight(
            venues=["coinbase", "gateio"],
            symbols=["BTC/USD"],
            do_private_check=True,
            probe_keys=["fetch_balance"],
        )
    )

    assert out["ok"] is False
    assert [row["exchange"] for row in out["private_connectivity"]] == ["coinbase", "gateio"]
    assert out["private_connectivity"][0]["ok"] is True
    assert out["private_connectivity"][1]["ok"] is False
    assert out["permission_probes"][0]["results"] == [{"probe": "fetch_balance"}]
import json

from services.diagnostics.config_restore import restore_missing_configs
from services.diagnostics.preflight import (
    PreflightConfig,
    diagnostics_text,
    run_preflight,
)


def test_restore_missing_configs_creates_missing_files(tmp_path):
    root = tmp_path
    tpl_dir = root / "config" / "templates"
    tpl_dir.mkdir(parents=True, exist_ok=True)
    (tpl_dir / "trading.yaml.default").write_text("symbols:\n  - BTC/USD\n", encoding="utf-8")
    (tpl_dir / ".env.template").write_text("EXAMPLE=1\n", encoding="utf-8")

    out = restore_missing_configs(str(root))

    assert out.ok is True
    assert str(root / "config" / "trading.yaml") in out.restored
    assert str(root / ".env.template") in out.restored
    assert (root / "config" / "trading.yaml").exists()
    assert (root / ".env.template").exists()


def test_restore_missing_configs_skips_existing_files(tmp_path):
    root = tmp_path
    tpl_dir = root / "config" / "templates"
    tpl_dir.mkdir(parents=True, exist_ok=True)
    (tpl_dir / "trading.yaml.default").write_text("symbols:\n  - BTC/USD\n", encoding="utf-8")
    (tpl_dir / ".env.template").write_text("EXAMPLE=1\n", encoding="utf-8")

    cfg = root / "config" / "trading.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("symbols:\n  - ETH/USD\n", encoding="utf-8")
    env_tpl = root / ".env.template"
    env_tpl.write_text("EXAMPLE=keep\n", encoding="utf-8")

    out = restore_missing_configs(str(root))

    assert out.ok is True
    assert str(cfg) in out.skipped
    assert str(env_tpl) in out.skipped
    assert cfg.read_text(encoding="utf-8") == "symbols:\n  - ETH/USD\n"
    assert env_tpl.read_text(encoding="utf-8") == "EXAMPLE=keep\n"


def test_diagnostics_text_is_sorted_json():
    payload = {"z": 1, "a": {"b": 2}}
    text = diagnostics_text(payload)

    assert json.loads(text) == payload
    assert text.index('"a"') < text.index('"z"')


def test_run_preflight_reports_blocked_when_config_missing(monkeypatch, tmp_path):
    from services.diagnostics import preflight as pf

    monkeypatch.setattr(pf, "ensure_dirs", lambda: None)
    monkeypatch.setattr(pf, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(pf, "can_bind", lambda host, port: True)
    monkeypatch.setattr(pf, "file_writable", lambda path: True)

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name in {"streamlit", "ccxt"}:
            return object()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    out = run_preflight(PreflightConfig(trading_yaml=str(tmp_path / "missing.yaml")))

    assert out["status"] == "BLOCKED"
    assert "missing config/trading.yaml" in out["blocked_reasons"]


def test_run_preflight_ok_when_requirements_present(monkeypatch, tmp_path):
    from services.diagnostics import preflight as pf

    cfg = tmp_path / "trading.yaml"
    cfg.write_text("symbols:\n  - BTC/USD\n", encoding="utf-8")

    monkeypatch.setattr(pf, "ensure_dirs", lambda: None)
    monkeypatch.setattr(pf, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(pf, "can_bind", lambda host, port: True)
    monkeypatch.setattr(pf, "file_writable", lambda path: True)

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name in {"streamlit", "ccxt"}:
            return object()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    out = run_preflight(PreflightConfig(trading_yaml=str(cfg)))

    assert out["status"] == "OK"
    assert out["blocked_reasons"] == []
    assert out["network"]["requested_port"] == 8501
    assert out["network"]["resolved_port"] == 8501


def test_run_preflight_auto_switches_when_requested_port_busy(monkeypatch, tmp_path):
    from services.diagnostics import preflight as pf

    cfg = tmp_path / "trading.yaml"
    cfg.write_text("symbols:\n  - BTC/USD\n", encoding="utf-8")

    monkeypatch.setattr(pf, "ensure_dirs", lambda: None)
    monkeypatch.setattr(pf, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(
        pf,
        "resolve_preferred_port",
        lambda host, port, max_offset=50: PortResolution(
            host=str(host),
            requested_port=int(port),
            resolved_port=8502,
            requested_available=False,
            auto_switched=True,
        ),
    )
    monkeypatch.setattr(pf, "can_bind", lambda host, port: int(port) == 8502)
    monkeypatch.setattr(pf, "file_writable", lambda path: True)

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name in {"streamlit", "ccxt"}:
            return object()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    out = run_preflight(PreflightConfig(trading_yaml=str(cfg)))

    assert out["status"] == "OK"
    assert out["blocked_reasons"] == []
    assert out["network"]["requested_port"] == 8501
    assert out["network"]["resolved_port"] == 8502
    assert out["network"]["auto_switched"] is True


def test_run_preflight_blocked_when_no_alternative_port_available(monkeypatch, tmp_path):
    from services.diagnostics import preflight as pf

    cfg = tmp_path / "trading.yaml"
    cfg.write_text("symbols:\n  - BTC/USD\n", encoding="utf-8")

    monkeypatch.setattr(pf, "ensure_dirs", lambda: None)
    monkeypatch.setattr(pf, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(
        pf,
        "resolve_preferred_port",
        lambda host, port, max_offset=50: PortResolution(
            host=str(host),
            requested_port=int(port),
            resolved_port=int(port),
            requested_available=False,
            auto_switched=False,
        ),
    )
    monkeypatch.setattr(pf, "can_bind", lambda host, port: False)
    monkeypatch.setattr(pf, "file_writable", lambda path: True)

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name in {"streamlit", "ccxt"}:
            return object()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    out = run_preflight(PreflightConfig(trading_yaml=str(cfg)))

    assert out["status"] == "BLOCKED"
    assert "no available UI port near 8501" in out["blocked_reasons"]


def test_run_preflight_blocked_when_import_missing(monkeypatch, tmp_path):
    from services.diagnostics import preflight as pf

    cfg = tmp_path / "trading.yaml"
    cfg.write_text("symbols:\n  - BTC/USD\n", encoding="utf-8")

    monkeypatch.setattr(pf, "ensure_dirs", lambda: None)
    monkeypatch.setattr(pf, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(pf, "can_bind", lambda host, port: True)
    monkeypatch.setattr(pf, "file_writable", lambda path: True)

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ModuleNotFoundError("streamlit")
        if name == "ccxt":
            return object()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    out = run_preflight(PreflightConfig(trading_yaml=str(cfg)))

    assert out["status"] == "BLOCKED"
    assert "streamlit not importable" in out["blocked_reasons"]
    assert out["imports"]["streamlit"].startswith("FAIL:")


def test_run_preflight_blocked_when_data_dir_not_writable(monkeypatch, tmp_path):
    from services.diagnostics import preflight as pf

    cfg = tmp_path / "trading.yaml"
    cfg.write_text("symbols:\n  - BTC/USD\n", encoding="utf-8")

    monkeypatch.setattr(pf, "ensure_dirs", lambda: None)
    monkeypatch.setattr(pf, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(pf, "can_bind", lambda host, port: True)
    monkeypatch.setattr(pf, "file_writable", lambda path: False)

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name in {"streamlit", "ccxt"}:
            return object()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    out = run_preflight(PreflightConfig(trading_yaml=str(cfg)))

    assert out["status"] == "OK"
    assert "data dir not writable" not in out["blocked_reasons"]


def test_run_preflight_blocked_when_ccxt_missing(monkeypatch, tmp_path):
    from services.diagnostics import preflight as pf

    cfg = tmp_path / "trading.yaml"
    cfg.write_text("symbols:\n  - BTC/USD\n", encoding="utf-8")

    monkeypatch.setattr(pf, "ensure_dirs", lambda: None)
    monkeypatch.setattr(pf, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(pf, "can_bind", lambda host, port: True)
    monkeypatch.setattr(pf, "file_writable", lambda path: True)

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "ccxt":
            raise ModuleNotFoundError("ccxt")
        if name == "streamlit":
            return object()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    out = run_preflight(PreflightConfig(trading_yaml=str(cfg)))

    assert out["status"] == "BLOCKED"
    assert "ccxt not importable" in out["blocked_reasons"]
    assert out["imports"]["ccxt"].startswith("FAIL:")


def test_restore_missing_configs_handles_missing_templates(tmp_path):
    root = tmp_path

    out = restore_missing_configs(str(root))

    assert out.ok is False
    assert out.restored == {}
    assert out.skipped == {}
    assert out.errors
