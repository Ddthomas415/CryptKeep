"""Contract-v2 synthetic histories; never read market outcomes."""
import hashlib
import json
import numpy as np

MODELS = ("iid", "overlap7", "persistent", "heavy_tail", "volatility_shift",
          "shared_unequal", "sparse", "random_missing", "loss_missing")
STREAMS = ("innovations", "event_noise", "counts", "missingness", "bootstrap",
           "heavy_tail_denominator")
MEANS = (0., .0025, .005, .01)


def stream_seed(stage, model, days, mean_index, trial, stream):
    if stage not in ("development", "confirmation", "benchmark"):
        raise ValueError("unknown stage")
    if model not in MODELS or stream not in STREAMS:
        raise ValueError("unknown model or stream")
    if days not in (90, 180, 365) or mean_index not in range(4) or trial < 0:
        raise ValueError("invalid history identifier")
    encoded = json.dumps([stage, model, days, mean_index, trial, stream],
                         ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return int.from_bytes(hashlib.sha256(encoded).digest()[:16], "big")


def generate(stage, model, days, mean_index, trial):
    def rng(stream):
        return np.random.Generator(np.random.PCG64(
            stream_seed(stage, model, days, mean_index, trial, stream)))
    innovations = rng("innovations")
    z = innovations.standard_normal(days+6)
    mu, sigma = MEANS[mean_index], .03
    if model == "heavy_tail":
        v = rng("heavy_tail_denominator").standard_normal((days+6, 5))
        z = z/np.sqrt(np.mean(v*v, axis=1))*np.sqrt(3/5)
    if model == "iid":
        shocks = sigma*z[:days]
    elif model == "persistent":
        state = sigma*innovations.standard_normal()
        shocks = np.empty(days)
        for t in range(days):
            state = .85*state+sigma*np.sqrt(1-.85**2)*z[t]
            shocks[t] = state
    else:
        scales = np.full(days+6, sigma)
        if model == "volatility_shift":
            scales[days//2:] *= 3
        shocks = np.convolve(z*scales, np.ones(7), mode="valid")/np.sqrt(7)
    counts = np.ones(days, dtype=int)
    if model == "shared_unequal":
        counts[days//2] = 20
    if model == "sparse":
        counts = (rng("counts").random(days) < .2).astype(int)
    day_index = np.repeat(np.arange(days), counts)
    truth = mu+shocks[day_index]
    if model == "shared_unequal":
        truth = truth+.01*rng("event_noise").standard_normal(len(truth))
    observed = np.ones(len(truth), dtype=bool)
    if model in ("random_missing", "loss_missing"):
        probability = .2 if model == "random_missing" else np.where(truth < 0, .8, .1)
        observed = rng("missingness").random(len(truth)) >= probability
    return {"day_index": day_index, "truth": truth, "observed": observed,
            "days": days, "refusal_only": model in MODELS[6:],
            "numpy_version": np.__version__}
