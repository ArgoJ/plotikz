"""Plotly to TikZ conversion subpackage."""

from .converter import PlotlyToTikz, plotly_to_tikz
from .heatmap_contour import extract_z_values, build_heatmap_contour_options, add_heatmap_halfcell_bounds
from .options_builder import build_axis_options, build_basic_layout_options
from .subplots import detect_subplots, build_axis_blocks
from .annotations import extract_annotations
from .html_parser import from_html

__all__ = [
    "PlotlyToTikz",
    "plotly_to_tikz",
    "extract_z_values",
    "build_heatmap_contour_options",
    "add_heatmap_halfcell_bounds",
    "build_axis_options",
    "build_basic_layout_options",
    "detect_subplots",
    "build_axis_blocks",
    "extract_annotations",
    "from_html",
]
