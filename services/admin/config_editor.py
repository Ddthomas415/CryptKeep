from __future__ import annotations
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, List
from services.audit.operator_event_journal import append_operator_event
from services.os.app_paths import config_dir, ensure_dirs

ensure_dirs()
CONFIG_PATH = config_dir() / "user.yaml"
BACKUP_PATH = config_dir() / "user.yaml.bak"
_LOG = logging.getLogger(__name__)

class ConfigLoadError(RuntimeError):
    """Raised when an existing user config cannot be trusted."""


def _config_load_error(path: Path, reason: str) -> ConfigLoadError:
    return ConfigLoadError(f"config_load_failed:{path}:{reason}")


def load_user_yaml(*, strict: bool = False) -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                return data
            if strict:
                raise _config_load_error(CONFIG_PATH, "not_mapping")
            return {}
    except ConfigLoadError:
        raise
    except Exception as e:
        if strict:
            raise _config_load_error(CONFIG_PATH, f"{type(e).__name__}:{e}") from e
        print(f"Error loading config: {type(e).__name__}: {e}")
        return {}


def _config_shape(cfg: Any) -> dict[str, Any]:
    if not isinstance(cfg, dict):
        return {"mapping": False, "section_count": 0, "section_names": []}
    return {
        "mapping": True,
        "section_count": len(cfg),
        "section_names": sorted(str(k) for k in cfg.keys()),
    }


def _current_config_shape() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"exists": False, "parse_ok": True, **_config_shape({})}
    try:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"exists": True, "parse_ok": False, **_config_shape({})}
    return {"exists": True, "parse_ok": True, **_config_shape(data)}


def _record_runtime_config_save(*, pre_state: dict[str, Any], post_state: dict[str, Any]) -> dict[str, Any]:
    try:
        event = append_operator_event(
            actor="operator",
            action="runtime_config_save",
            target="user.yaml",
            result="success",
            reason="save_user_yaml",
            pre_state=pre_state,
            post_state=post_state,
            source="services.admin.config_editor",
            extra={"config_payload_logged": False},
        )
        return {"ok": True, "event_id": event.get("event_id"), "path": event.get("path")}
    except Exception as exc:
        _LOG.warning(
            "runtime_config_save operator event journal failed: %s: %s",
            type(exc).__name__,
            exc,
        )
        return {"ok": False, "reason": f"operator_event_write_failed:{type(exc).__name__}"}


def _restore_config_bytes(previous: bytes | None) -> dict[str, Any]:
    try:
        if previous is None:
            if CONFIG_PATH.exists():
                CONFIG_PATH.unlink()
            return {"ok": True, "exists": False}
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_bytes(previous)
        return {"ok": True, "exists": True}
    except Exception as exc:
        return {"ok": False, "reason": f"rollback_failed:{type(exc).__name__}"}


def save_user_yaml(cfg: Dict[str, Any], dry_run: bool = False) -> Tuple[bool, str]:
    if not isinstance(cfg, dict):
        return False, "cfg must be dict"
    try:
        pre_state = _current_config_shape()
        previous_bytes = CONFIG_PATH.read_bytes() if CONFIG_PATH.exists() else None
        if CONFIG_PATH.exists():
            BACKUP_PATH.write_bytes(CONFIG_PATH.read_bytes())
        if dry_run:
            return True, "Dry run OK"
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
        operator_event = _record_runtime_config_save(
            pre_state=pre_state,
            post_state={"exists": True, "parse_ok": True, **_config_shape(cfg)},
        )
        if not bool(operator_event.get("ok")):
            rollback = _restore_config_bytes(previous_bytes)
            if rollback.get("ok"):
                return False, "operator_event_write_failed_runtime_config_rolled_back"
            return (
                False,
                "operator_event_write_failed_runtime_config_rollback_failed:"
                f"{rollback.get('reason')}",
            )
        return True, "Saved"
    except Exception as e:
        return False, f"Save failed: {type(e).__name__}: {e}"

def validate_user_yaml(cfg: Dict[str, Any] = None) -> Tuple[bool, List[str], List[str]]:
    if cfg is None:
        cfg = load_user_yaml()
    errors = []
    warnings = []

    def is_bool(v): return isinstance(v, bool)
    def is_float(v): return isinstance(v, (int, float))
    def is_int(v): return isinstance(v, int)
    def is_str(v): return isinstance(v, str)
    def is_list(v): return isinstance(v, list)
    def is_dict(v): return isinstance(v, dict)

    # preflight
    pf = cfg.get("preflight", {})
    if pf and not is_dict(pf):
        errors.append("preflight:must_be_mapping")
    if is_dict(pf):
        if "venues" in pf and not is_list(pf["venues"]):
            errors.append("preflight.venues:must_be_list")
        if "symbols" in pf and not is_list(pf["symbols"]):
            errors.append("preflight.symbols:must_be_list")

    # paper_execution
    pe = cfg.get("paper_execution", {})
    if pe and not is_dict(pe):
        errors.append("paper_execution:must_be_mapping")
    if is_dict(pe):
        if "enabled" in pe and not is_bool(pe["enabled"]):
            errors.append("paper_execution.enabled:must_be_bool")
        for k in ("poll_sec", "max_per_loop"):
            if k in pe and not is_int(pe[k]):
                errors.append(f"paper_execution.{k}:must_be_int")
        for k in ("fee_bps", "slippage_bps"):
            if k in pe and not is_float(pe[k]):
                errors.append(f"paper_execution.{k}:must_be_float")

    # signals
    sg = cfg.get("signals", {})
    if sg and not is_dict(sg):
        errors.append("signals:must_be_mapping")
    if is_dict(sg):
        if "auto_route_to_paper" in sg and not is_bool(sg["auto_route_to_paper"]):
            errors.append("signals.auto_route_to_paper:must_be_bool")
        for k in ("allowed_sources", "allowed_authors", "allowed_symbols"):
            if k in sg and not is_list(sg[k]):
                errors.append(f"signals.{k}:must_be_list")
        for k in ("default_venue", "order_type"):
            if k in sg and not is_str(sg[k]):
                errors.append(f"signals.{k}:must_be_string")
        if "default_qty" in sg and not is_float(sg["default_qty"]):
            errors.append("signals.default_qty:must_be_float")

    # signals_learning
    sl = cfg.get("signals_learning", {})
    if sl and not is_dict(sl):
        errors.append("signals_learning:must_be_mapping")
    if is_dict(sl):
        for k in ("enabled", "scale_qty"):
            if k in sl and not is_bool(sl[k]):
                errors.append(f"signals_learning.{k}:must_be_bool")
        for k in ("min_n_scored", "horizon_candles"):
            if k in sl and not is_int(sl[k]):
                errors.append(f"signals_learning.{k}:must_be_int")
        for k in ("min_hit_rate", "qty_scale_min", "qty_scale_max"):
            if k in sl and not is_float(sl[k]):
                errors.append(f"signals_learning.{k}:must_be_float")
        if "timeframe" in sl and not is_str(sl["timeframe"]):
            errors.append("signals_learning.timeframe:must_be_string")
        if "venue" in sl and not is_str(sl["venue"]):
            errors.append("signals_learning.venue:must_be_string")

    # meta_strategy
    ms = cfg.get("meta_strategy", {})
    if ms and not is_dict(ms):
        errors.append("meta_strategy:must_be_mapping")

    # updates
    up = cfg.get("updates", {})
    if up and not is_dict(up):
        errors.append("updates:must_be_mapping")
    if is_dict(up):
        for k in ("enabled", "allow_download"):
            if k in up and not is_bool(up[k]):
                errors.append(f"updates.{k}:must_be_bool")
        if "timeout_sec" in up and not is_float(up["timeout_sec"]):
            errors.append("updates.timeout_sec:must_be_float")
        if "channel_url" in up and not is_str(up["channel_url"]):
            errors.append("updates.channel_url:must_be_string")

    ok = len(errors) == 0
    return ok, errors, warnings

if __name__ == "__main__":
    cfg = load_user_yaml()
    ok, errs, warns = validate_user_yaml(cfg)
    print(f"Validation OK: {ok}")
    if errs:
        print("Errors:", errs)
    if warns:
        print("Warnings:", warns)

def ensure_user_yaml_exists() -> bool:
    if CONFIG_PATH.exists():
        return True
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text("# Default config\n", encoding="utf-8")
        return True
    except Exception:
        return False

def list_backups() -> list[str]:
    return [str(p) for p in CONFIG_PATH.parent.glob("user.yaml.bak*") if p.is_file()]

def restore_backup(backup_path: str) -> bool:
    try:
        backup = Path(backup_path)
        if not backup.exists():
            return False
        CONFIG_PATH.write_bytes(backup.read_bytes())
        return True
    except Exception:
        return False

def set_armed(state: bool) -> dict:
    from services.admin.kill_switch import set_armed as _set_armed
    return _set_armed(bool(state), note="config_editor_compat")

def read_health(service: str = "system") -> dict:
    from services.admin.health import read_health as _read_health
    return _read_health(str(service))

def maybe_auto_update_state_on_snapshot(snapshot: dict | None = None) -> dict:
    from services.admin.state_report import maybe_auto_update_state_on_snapshot as _update
    tag = ""
    if isinstance(snapshot, dict):
        tag = str(snapshot.get("tag") or snapshot.get("source") or "")
    return _update(tag=tag)
