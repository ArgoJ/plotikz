"""Trace handlers for plotikz."""

from .base import TraceHandler
from .scatter import ScatterHandler
from .bar import BarHandler
from .heatmap import HeatmapHandler
from .generic import GenericHandler

__all__ = [
    "TraceHandler",
    "ScatterHandler",
    "BarHandler",
    "HeatmapHandler",
    "GenericHandler",
]
