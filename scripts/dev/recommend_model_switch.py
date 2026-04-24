from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)




import json
from pathlib import Path

from services.config_loader import load_runtime_trading_config
from services.os.app_paths import data_dir, ensure_dirs
from services.learning.model_registry import ModelRegistry, RegistryCfg

ensure_dirs()
_DROOT = data_dir()
RECO_PATH = _DROOT / "learning" / "recommended_model.json"

def _load_eval(model_id: str) -> dict | None:
    p1 = _DROOT / "models" / model_id / "walk_forward_report.json"
    p2 = _DROOT / "models" / model_id / "eval_report.json"
    for p in (p1, p2):
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return None
    return None

def _score_wf(rep: dict) -> tuple[float,float,int]:
    try:
        return (float(rep["auc"]["median"]), float(rep["auc"]["stdev"]), int(rep.get("n_windows_used") or 0))
    except Exception:
        return (float("nan"), float("inf"), 0)

def main() -> int:
    cfg = load_runtime_trading_config()
    learn = cfg.get("learning") or {}

    min_windows = int(learn.get("wf_min_windows_used") or 3)
    max_stdev = float(learn.get("wf_max_auc_stdev") or 0.08)
    min_delta = float(learn.get("wf_min_auc_delta_to_switch") or 0.01)

    current_id = (learn.get("active_model_id") or "").strip() or None
    cur_rep = _load_eval(current_id) if current_id else None
    cur_med = None
    if cur_rep and isinstance(cur_rep.get("auc"), dict) and "median" in cur_rep["auc"]:
        cur_med, _, _ = _score_wf(cur_rep)

    reg = ModelRegistry(RegistryCfg())
    models = reg.list()

    candidates = []
    for m in models:
        mid = str(m.get("model_id"))
        rep = _load_eval(mid)
        if not rep or not (isinstance(rep.get("auc"), dict) and "median" in rep["auc"]):
            continue
        med, sd, wused = _score_wf(rep)
        candidates.append({"model_id": mid, "name": m.get("name"), "median_auc": med, "stdev_auc": sd, "windows_used": wused})

    if not candidates:
        print({"ok": False, "note": "no_candidates_with_eval"})
        return 2

    candidates.sort(key=lambda x: (-x["median_auc"], x["stdev_auc"]))
    best = candidates[0]

    # rules
    if int(best["windows_used"]) < min_windows:
        out = {"ok": True, "note": "no_switch_candidate_too_few_windows", "best": best, "rules": {"min_windows": min_windows}}
    elif float(best["stdev_auc"]) > max_stdev:
        out = {"ok": True, "note": "no_switch_candidate_too_volatile", "best": best, "rules": {"max_stdev": max_stdev}}
    elif cur_med is not None and float(best["median_auc"]) < float(cur_med) + min_delta:
        out = {"ok": True, "note": "no_switch_not_enough_improvement", "current": {"model_id": current_id, "median_auc": cur_med}, "best": best, "rules": {"min_delta": min_delta}}
    else:
        out = {"ok": True, "note": "switch_recommended", "current_model_id": current_id, "best": best, "rules": {"min_windows": min_windows, "max_stdev": max_stdev, "min_delta": min_delta}}

    RECO_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECO_PATH.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
