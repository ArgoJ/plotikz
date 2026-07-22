"""Trace handlers for plotikz."""

from .base import TraceHandler
from .scatter import ScatterHandler
from .bar import BarHandler
from .heatmap import HeatmapHandler
from .contour import ContourHandler
from .parcoords import ParcoordsHandler
from .generic import GenericHandler

__all__ = [
    "TraceHandler",
    "ScatterHandler",
    "BarHandler",
    "HeatmapHandler",
    "ContourHandler",
    "ParcoordsHandler",
    "GenericHandler",
]

