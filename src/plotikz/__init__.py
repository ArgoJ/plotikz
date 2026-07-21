"""plotikz: Convert Plotly figures into clean LaTeX/TikZ code using PGFPlots."""

from .converter import PlotlyToTikz, to_tikz
from .registry import (
    TraceHandler,
    ScatterHandler,
    BarHandler,
    HeatmapHandler,
    GenericHandler,
    TraceRegistry,
    default_registry,
)

__all__ = [
    "PlotlyToTikz",
    "to_tikz",
    "TraceHandler",
    "ScatterHandler",
    "BarHandler",
    "HeatmapHandler",
    "GenericHandler",
    "TraceRegistry",
    "default_registry",
]

__version__ = "0.1.0"
