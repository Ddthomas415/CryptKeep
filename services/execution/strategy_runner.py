from __future__ import annotations

_PLACEHOLDER_ERROR = (
    "services.execution.strategy_runner is a deprecated placeholder and must not be used for live or paper "
    "runtime execution. Use services.strategy_runner.ema_crossover_runner instead."
)


def _raise_placeholder_error(*args, **kwargs):
    raise RuntimeError(_PLACEHOLDER_ERROR)


run_once = _raise_placeholder_error
request_shutdown = _raise_placeholder_error
run_forever = _raise_placeholder_error
run = _raise_placeholder_error
main = _raise_placeholder_error


if __name__ == "__main__":
    raise RuntimeError(_PLACEHOLDER_ERROR)
