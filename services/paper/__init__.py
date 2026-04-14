"""Transitional package — deprecated, removal target 2026-07-01."""
import warnings
warnings.warn(
    f"{__name__} is a transitional package scheduled for removal 2026-07-01. "
    "See docs/ARCHITECTURE.md for canonical replacements.",
    DeprecationWarning,
    stacklevel=2,
)
