# Export all public functions/classes
from .service_manager import specs_default, start_service, stop_service, is_running, start_stack
from .logging_control import set_log_level, set_log_rotate_bytes, rotate_logs
from .panic import panic_stop_execution

# Safe fallback for service_registry (if used elsewhere)
try:
    from .service_registry import service_registry
except ImportError:
    service_registry = None
