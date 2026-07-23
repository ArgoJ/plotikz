"""plotikz - Convert Plotly and Matplotlib figures to LaTeX TikZ/PGFPlots code."""

from .unified import to_tikz
from .plotly import PlotlyToTikz, from_html
from .matplotlib import MatplotlibToTikz, from_pyplot
from .registry import TraceRegistry, default_registry
from .handlers.base import TraceHandler

__all__ = [
    "to_tikz",
    "from_html",
    "from_pyplot",
    "PlotlyToTikz",
    "MatplotlibToTikz",
    "TraceRegistry",
    "default_registry",
    "TraceHandler",
]
