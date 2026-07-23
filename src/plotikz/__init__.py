"""plotikz - Convert Plotly figures and HTML files to LaTeX TikZ/PGFPlots code."""

from .plotly import PlotlyToTikz, to_tikz, from_html
from .registry import TraceRegistry, default_registry
from .handlers.base import TraceHandler

__all__ = [
    "PlotlyToTikz",
    "to_tikz",
    "from_html",
    "TraceRegistry",
    "default_registry",
    "TraceHandler",
]
