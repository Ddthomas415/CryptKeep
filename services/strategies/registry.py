# Phase IH: Strategy Registry

STRATEGIES = {}

def register(name):
    def deco(fn):
        STRATEGIES[name] = fn
        return fn
    return deco

# --- compat shim: legacy entrypoint expected by scripts/run_bot_safe.py ---
def get_strategy(name, *args, **kwargs):
    """Return a strategy by name.

    This is a compatibility wrapper. It tries common registry patterns without
    assuming one specific internal API shape.
    """
    # 1) Prefer explicit functions if they exist
    for fn_name in (
        "resolve_strategy", "build_strategy", "make_strategy", "create_strategy",
        "strategy", "get", "resolve"
    ):
        fn = globals().get(fn_name) or globals().get(f"{fn_name}_strategy")
        if callable(fn):
            try:
                return fn(name, *args, **kwargs)
            except TypeError:
                # older signatures may only accept name
                return fn(name)

    # 2) Fall back to common dict registries
    for reg_name in ("REGISTRY", "STRATEGIES", "strategies", "registry"):
        reg_obj = globals().get(reg_name)
        if isinstance(reg_obj, dict):
            if name in reg_obj:
                return reg_obj[name]
    raise KeyError(f"Unknown strategy: {name!r}")

