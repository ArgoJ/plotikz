"""Plotly to TikZ conversion subpackage."""

from .converter import PlotlyToTikz, plotly_to_tikz
from .heatmap_contour import extract_z_values, build_heatmap_contour_options, add_heatmap_halfcell_bounds
from .options_builder import build_axis_options, build_basic_layout_options
from .subplots import detect_subplots, build_axis_blocks
from .annotations import extract_annotations
from .shapes import extract_shapes, format_shape_to_tikz, parse_svg_path_to_tikz
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
    "extract_shapes",
    "format_shape_to_tikz",
    "parse_svg_path_to_tikz",
    "from_html",
]
