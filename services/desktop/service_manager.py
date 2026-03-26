
"""
Legacy compatibility shim for older desktop service-manager callers.

Current operator/service control scripts use:

- scripts/service_ctl.py -> services.desktop.simple_service_manager

This module remains only as a compatibility surface for any residual imports
that still expect a `services.desktop.service_manager` module shape.
"""

def specs_default():
    # Try common internal providers
    for n in ("specs_default", "specs", "get_specs", "default_specs"):
        fn = globals().get(n)
        if callable(fn) and fn is not specs_default:
            return fn()
    # Try ServiceManager style
    mgr = globals().get("ServiceManager")
    if mgr:
        m = mgr()
        for n in ("specs_default", "specs", "get_specs", "default_specs"):
            fn = getattr(m, n, None)
            if callable(fn):
                return fn()
    return {}

def start_service(name: str, **kwargs):
    fn = globals().get("start") or globals().get("start_service_impl")
    if callable(fn):
        return fn(name, **kwargs)
    mgr = globals().get("ServiceManager")
    if mgr:
        m = mgr()
        fn = getattr(m, "start_service", None) or getattr(m, "start", None)
        if callable(fn):
            return fn(name, **kwargs)
    raise RuntimeError("service_manager: start_service not implemented")

def stop_service(name: str, **kwargs):
    fn = globals().get("stop") or globals().get("stop_service_impl")
    if callable(fn):
        return fn(name, **kwargs)
    mgr = globals().get("ServiceManager")
    if mgr:
        m = mgr()
        fn = getattr(m, "stop_service", None) or getattr(m, "stop", None)
        if callable(fn):
            return fn(name, **kwargs)
    raise RuntimeError("service_manager: stop_service not implemented")

def is_running(name: str) -> bool:
    fn = globals().get("is_running_impl")
    if callable(fn):
        return bool(fn(name))
    mgr = globals().get("ServiceManager")
    if mgr:
        m = mgr()
        fn = getattr(m, "is_running", None) or getattr(m, "running", None)
        if callable(fn):
            return bool(fn(name))
    return False
