"""Trace handler registry for plotikz."""

from typing import List

from .handlers import (
    TraceHandler,
    ScatterHandler,
    BarHandler,
    HeatmapHandler,
    GenericHandler,
)
from .utils import (
    format_color,
    escape_tex,
    clean_val,
    format_coord_val,
)


class TraceRegistry:
    """Registry for trace handlers."""

    def __init__(self):
        self._handlers: List[TraceHandler] = []

    def register(self, handler: TraceHandler):
        """Register a new trace handler."""
        self._handlers.append(handler)

    def get_handler(self, trace_type: str) -> TraceHandler:
        """Find handler for trace_type (searches in reverse order for overrides)."""
        for handler in reversed(self._handlers):
            if handler.can_handle(trace_type):
                return handler
        return GenericHandler()


# Default global registry pre-populated with standard handlers
default_registry = TraceRegistry()
default_registry.register(ScatterHandler())
default_registry.register(BarHandler())
default_registry.register(HeatmapHandler())

__all__ = [
    "TraceHandler",
    "ScatterHandler",
    "BarHandler",
    "HeatmapHandler",
    "GenericHandler",
    "TraceRegistry",
    "default_registry",
    "format_color",
    "escape_tex",
    "clean_val",
    "format_coord_val",
]
