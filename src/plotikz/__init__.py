"""plotikz: Convert Plotly figures into clean LaTeX/TikZ code using PGFPlots."""

from .plotly_converter import PlotlyToTikz, to_tikz
from .html_parser import from_html, parse_html_to_figure
from .handlers import (
    TraceHandler,
    ScatterHandler,
    BarHandler,
    HeatmapHandler,
    ContourHandler,
    ParcoordsHandler,
    GenericHandler,
)
from .registry import (
    TraceRegistry,
    default_registry,
)

__all__ = [
    "PlotlyToTikz",
    "to_tikz",
    "from_html",
    "parse_html_to_figure",
    "TraceHandler",
    "ScatterHandler",
    "BarHandler",
    "HeatmapHandler",
    "ContourHandler",
    "ParcoordsHandler",
    "GenericHandler",
    "TraceRegistry",
    "default_registry",
]

__version__ = "0.1.0"
