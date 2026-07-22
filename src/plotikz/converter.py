"""Module converter.py re-exports PlotlyToTikz for backward compatibility.
Please import from plotikz.plotly_converter directly.
"""

from .plotly_converter import PlotlyToTikz, to_tikz

__all__ = ["PlotlyToTikz", "to_tikz"]
