"""Translation of Matplotlib Figure/Axes into plotikz structures."""

from typing import Any, Dict, List, Tuple
from .extractors import extract_lines, extract_collections, extract_layout


def figure_to_plotikz_data(fig: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Translate Matplotlib Figure or Axes into a list of trace dictionaries and layout dictionary.
    """
    # If passed an Axes object, find parent figure or process axes directly
    axes_list = []
    if hasattr(fig, "get_axes"):
        axes_list = fig.get_axes()
    elif hasattr(fig, "lines") and hasattr(fig, "get_title"):
        axes_list = [fig]

    if not axes_list:
        return [], {}

    # For single axes figure
    if len(axes_list) == 1:
        ax = axes_list[0]
        traces = []
        traces.extend(extract_lines(ax))
        traces.extend(extract_collections(ax))
        layout = extract_layout(ax)
        return traces, layout

    # For multi-axes figure / subplots
    traces = []
    layout = {}

    for idx, ax in enumerate(axes_list, start=1):
        xaxis_key = f"x{idx}" if idx > 1 else "x"
        yaxis_key = f"y{idx}" if idx > 1 else "y"

        ax_traces = []
        ax_traces.extend(extract_lines(ax))
        ax_traces.extend(extract_collections(ax))

        for t in ax_traces:
            t["xaxis"] = xaxis_key
            t["yaxis"] = yaxis_key
            traces.append(t)

        ax_layout = extract_layout(ax)
        if idx == 1 and ax_layout.get("title"):
            layout["title"] = ax_layout["title"]

        xaxis_dict = ax_layout.get("xaxis", {})
        yaxis_dict = ax_layout.get("yaxis", {})

        layout[f"xaxis{idx}" if idx > 1 else "xaxis"] = xaxis_dict
        layout[f"yaxis{idx}" if idx > 1 else "yaxis"] = yaxis_dict

    return traces, layout
