"""Budgeted fresh synthetic pilot only; no market access or scoring authority."""
import argparse
import collections
import hashlib
import json
import math
import platform
import time
from datetime import date, timedelta
from pathlib import Path

from scripts.research import cmc_calibration_v3 as models
from scripts.research import cmc_cohort_completeness as completeness
from scripts.research import cmc_paired_ratio_candidate as candidate

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research/research_corrections_20261009/cmc_paired_ratio_pilot_20261010"
PLAN = ROOT / "docs/research/cmc_trending_log/paired_ratio_pilot_manifest_20261010.md"
STAGE = "paired_ratio_pilot_20261010"
BENCH = "paired_ratio_benchmark_20261010"
LENGTHS = (90, 365)
TRIALS = 20
GENERATOR_SHA = "26fb3ce192f93416f215d1c8ec2e3f7bb39489ac85c9b1f20ebc7843858369d4"
EXPECTED = {(m, n, t) for m in models.MODELS for n in LENGTHS for t in range(TRIALS)}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity():
    if digest(models.__file__) != GENERATOR_SHA:
        raise ValueError("historical generator changed")
    return {"generator": GENERATOR_SHA, "candidate": digest(candidate.__file__),
            "completeness": digest(completeness.__file__), "runner": digest(__file__),
            "contract": digest(candidate.CONTRACT), "manifest": digest(PLAN),
            "python": platform.python_version(), "numpy": models.np.__version__}


def write_new(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)


def accepted(path, ident):
    receipt = json.loads(path.read_bytes())
    if (receipt.get("identity") != ident or receipt.get("status") not in
            ("ACCEPTED", "ACCEPTED_WITH_RISK")):
        raise ValueError("matching independent review required")


def stream_audit():
    seeds = set()
    count = 0
    for stage, names, trials in ((BENCH, models.SUPPORTED, range(1)),
                                (STAGE, models.MODELS, range(TRIALS))):
        for model in names:
            for days in LENGTHS:
                for trial in trials:
                    for stream in models.STREAMS:
                        seed = models.stream_seed(stage, model, days, 0, trial, stream,
                                                  allowed=(STAGE, BENCH))
                        if seed in seeds:
                            raise ValueError("stream seed collision")
                        seeds.add(seed)
                        count += 1
    return count


def evaluate(stage, model, days, trial):
    history = models.generate(stage, model, days, 0, trial, allowed=(STAGE, BENCH))
    if history["refusal_only"]:
        return {"status": "REFUSED", "reason": "registered_refusal_model_policy"}
    calendar = [(date(2000, 1, 1) + timedelta(days=i)).isoformat() for i in range(days)]
    events = [{"utc_day": calendar[int(day)], "event_id": str(i),
               "eligibility": "ELIGIBLE", "outcome_status": "AVAILABLE" if obs else "MISSING",
               "excess_return": float(value) if obs else None}
              for i, (day, value, obs) in enumerate(zip(history["day_index"], history["truth"], history["observed"]))]
    audit = completeness.audit_calendar(events, calendar, calendar[0], calendar[-1], calendar[-1])
    if audit["status"] != "COMPLETE_FULL_COHORT":
        return {"status": "INCOMPLETE", "reason": "missing_synthetic_outcomes"}
    seed = models.stream_seed(stage, model, days, 0, trial, "bootstrap", allowed=(STAGE, BENCH))
    result = candidate.candidate_interval(audit, seed=seed)
    return {"status": result["status"], "positive": bool(result["status"] == "CANDIDATE_INTERVAL"
            and result["interval"][0] > 0), "candidate_result": result}


def benchmark():
    ident = identity()
    accepted(OUT / "runner_review.json", ident)
    path = OUT / "benchmark.json"
    if path.exists():
        previous = json.loads(path.read_bytes())
        validate_benchmark(previous)
        return previous
    streams = stream_audit()
    durations = []
    for model in models.SUPPORTED:
        for days in LENGTHS:
            start = time.monotonic()
            try:
                evaluate(BENCH, model, days, 0)
            except Exception as exc:
                durations.append({"model":model,"days":days,"seconds":time.monotonic()-start})
                write_new(path,{"identity":ident,"stage":BENCH,"status":"BENCHMARK_FAILED",
                    "durations":durations,"error":type(exc).__name__,"reason":str(exc),
                    "scoring_authorized":False})
                raise ValueError("benchmark failure persisted; do not retry") from exc
            durations.append({"model": model, "days": days, "seconds": time.monotonic()-start})
    projection = 2 * TRIALS * sum(r["seconds"] for r in durations) + 10
    result = {"identity": ident, "stage": BENCH, "status":"BENCHMARK_COMPLETE", "durations": durations,
              "unique_stream_seeds": streams, "projected_seconds": projection,
              "within_budget": projection <= 600, "scoring_authorized": False}
    validate_benchmark(result)
    write_new(path, result)
    return result


def validate_benchmark(value):
    expected={(m,n) for m in models.SUPPORTED for n in LENGTHS}
    if (value.get("identity")!=identity() or value.get("stage")!=BENCH
            or value.get("status")!="BENCHMARK_COMPLETE"
            or value.get("scoring_authorized") is not False
            or type(value.get("unique_stream_seeds")) is not int
            or value["unique_stream_seeds"]!=2232):
        raise ValueError("invalid benchmark identity or failed receipt")
    seen=set()
    for row in value.get("durations",[]):
        cell=(row.get("model"),row.get("days"))
        seconds=row.get("seconds")
        if (type(cell[0]) is not str or type(cell[1]) is not int
                or cell not in expected or cell in seen
                or type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0):
            raise ValueError("invalid benchmark duration grid")
        seen.add(cell)
    projection=2*TRIALS*sum(r["seconds"] for r in value.get("durations",[]))+10
    if (seen!=expected or type(value.get("projected_seconds")) not in (int,float)
            or value["projected_seconds"]!=projection
            or type(value.get("within_budget")) is not bool
            or value["within_budget"]!=(projection<=600)):
        raise ValueError("benchmark projection mismatch")
    return value


def budget_context():
    ident=identity()
    accepted(OUT/"runner_review.json",ident)
    value=validate_benchmark(json.loads((OUT/"benchmark.json").read_bytes()))
    accepted(OUT/"budget_review.json",{"identity":ident,"benchmark_sha256":digest(OUT/"benchmark.json")})
    if not value["within_budget"]:
        raise ValueError("budget exceeded")
    return value


def validate(part):
    cell = (part.get("model"), part.get("days"), part.get("trial"))
    if (type(cell[0]) is not str or type(cell[1]) is not int or type(cell[2]) is not int
            or cell not in EXPECTED or part.get("identity") != identity()
            or part.get("stage") != STAGE or type(part.get("mean_index")) is not int or part["mean_index"] != 0
            or part.get("scoring_authorized") is not False):
        raise ValueError("trial identity mismatch")
    seconds = part.get("seconds")
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError("invalid trial duration")
    result = part.get("result", {})
    if result.get("status") not in ("REFUSED", "INCOMPLETE", "DEGENERATE", "CANDIDATE_INTERVAL", "FAILED_ATTEMPT"):
        raise ValueError("invalid trial disposition")
    if result["status"]=="FAILED_ATTEMPT":
        if not isinstance(result.get("error"),str) or not isinstance(result.get("reason"),str):
            raise ValueError("invalid failure record")
        return cell
    if result["status"]=="REFUSED":
        if cell[0] in models.SUPPORTED or result.get("reason")!="registered_refusal_model_policy":
            raise ValueError("invalid refusal policy")
        return cell
    if cell[0] not in models.SUPPORTED:
        raise ValueError("refusal policy changed")
    if result["status"] in ("CANDIDATE_INTERVAL","DEGENERATE","INCOMPLETE"):
        inner = result["candidate_result"]
        interval = inner["interval"]
        expected_seed=models.stream_seed(STAGE,cell[0],cell[1],0,cell[2],"bootstrap",allowed=(STAGE,))
        ident=identity()
        expected_events=cell[1]+(19 if cell[0]=="shared_unequal" else 0)
        exact={"calendar_days":cell[1],"block_length":candidate.block_length(cell[1]),
               "replicates":2000,"seed":expected_seed,"eligible_events":expected_events}
        if (any(type(inner.get(k)) is not int or inner[k]!=v for k,v in exact.items())
                or inner.get("contract_sha256")!=ident["contract"]
                or inner.get("implementation_sha256")!=ident["candidate"]
                or inner.get("numpy_version")!=ident["numpy"] or inner.get("python_version")!=ident["python"]
                or not isinstance(inner.get("input_sha256"),str) or len(inner["input_sha256"])!=64
                or any(c not in "0123456789abcdef" for c in inner["input_sha256"])
                or type(inner.get("event_weighted_mean")) not in (int,float)
                or not math.isfinite(inner["event_weighted_mean"])
                or inner.get("qualification")!="UNVALIDATED_CONDITIONAL_METHOD_CANDIDATE"
                or inner.get("status") != result["status"]
                or inner.get("scoring_authorized") is not False
                or type(result.get("positive")) is not bool):
            raise ValueError("invalid candidate metadata")
        completed=inner.get("completed_replicates")
        if type(completed) is not int or not isinstance(inner.get("reason"),str):
            raise ValueError("invalid replicate disposition")
        if result["status"]=="INCOMPLETE":
            if interval is not None or not 0<=completed<=2000 or result["positive"]:
                raise ValueError("invalid incomplete interval")
            return cell
        if (completed!=2000 or not isinstance(interval,list) or len(interval)!=2
                or any(type(x) not in (int,float) or not math.isfinite(x) for x in interval)
                or (interval[0]==interval[1])!=(result["status"]=="DEGENERATE")
                or interval[0]>interval[1]
                or result["positive"]!=(result["status"]=="CANDIDATE_INTERVAL" and interval[0]>0)):
            raise ValueError("invalid candidate interval")
    return cell


def parts():
    saved = {}
    for path in (OUT / "trials").glob("*.json"):
        part = json.loads(path.read_bytes())
        cell = validate(part)
        if cell in saved or path.name != f"{cell[0]}_{cell[1]}_{cell[2]}.json":
            raise ValueError("duplicate or misnamed trial")
        saved[cell] = part
    return saved


def pilot():
    ident = identity()
    budget=budget_context()
    saved = parts()
    if any(p["result"]["status"]=="FAILED_ATTEMPT" for p in saved.values()):
        return {"status":"PILOT_ABORTED_FAILURE","histories":len(saved)}
    elapsed = sum(p["seconds"] for p in saved.values())+sum(r["seconds"] for r in budget["durations"])
    start = time.monotonic()
    for cell in sorted(EXPECTED):
        if cell in saved:
            continue
        if elapsed + time.monotonic()-start >= 600:
            return {"status": "PILOT_INCOMPLETE_BUDGET", "histories": len(saved)}
        model, days, trial = cell
        before = time.monotonic()
        try:
            result = evaluate(STAGE, model, days, trial)
        except Exception as exc:
            result={"status":"FAILED_ATTEMPT","error":type(exc).__name__,"reason":str(exc)}
        part = {"identity": ident, "stage": STAGE, "model": model, "days": days,
                "trial": trial, "mean_index": 0, "seconds": time.monotonic()-before,
                "result": result, "scoring_authorized": False}
        validate(part)
        write_new(OUT / "trials" / f"{model}_{days}_{trial}.json", part)
        saved[cell] = part
        if result["status"]=="FAILED_ATTEMPT":
            return {"status":"PILOT_ABORTED_FAILURE","histories":len(saved)}
    return summarize()


def summarize():
    budget_context()
    saved = parts()
    if set(saved) != EXPECTED:
        raise ValueError("incomplete pilot grid")
    cells = []
    for model in models.MODELS:
        for days in LENGTHS:
            group = [saved[model,days,t]["result"] for t in range(TRIALS)]
            statuses = dict(collections.Counter(r["status"] for r in group))
            positives = sum(r.get("positive",False) for r in group if r["status"] == "CANDIDATE_INTERVAL")
            flagged = (statuses.get("CANDIDATE_INTERVAL",0) != TRIALS or positives > 2) if model in models.SUPPORTED else statuses.get("REFUSED",0) != TRIALS
            cells.append({"model":model,"days":days,"histories":TRIALS,"status_counts":statuses,
                          "positives":positives,"wilson95":models.wilson(positives,TRIALS),"flagged":flagged})
    result = {"identity":identity(),"status":"PILOT_SCREEN_FAILED" if any(c["flagged"] for c in cells) else "SMALL_PILOT_ONLY",
              "histories":len(saved),"cells":cells,"scoring_authorized":False,"no_power_study":True}
    path = OUT / "summary.json"
    if path.exists():
        if json.loads(path.read_bytes()) != json.loads(json.dumps(result)):
            raise ValueError("summary mismatch")
    else:
        write_new(path,result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("benchmark","pilot","summarize"))
    print(json.dumps(globals()[parser.parse_args().mode](),indent=2))
