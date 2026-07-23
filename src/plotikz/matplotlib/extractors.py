"""Extractors for Matplotlib Figure and Axes objects."""

from typing import Dict, Any, List, Tuple, Optional
import matplotlib.colors as mcolors
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.collections as mcoll
import numpy as np


def rgba_to_hex_or_rgb(color: Any) -> str:
    """Convert Matplotlib color specification to hex or RGB string."""
    try:
        rgba = mcolors.to_rgba(color)
        r, g, b, a = [int(round(c * 255)) for c in rgba]
        if a < 255:
            return f"rgba({r},{g},{b},{rgba[3]:.2f})"
        return f"rgb({r},{g},{b})"
    except Exception:
        return "#1f77b4"


def map_linestyle(ls: str) -> str:
    """Map Matplotlib linestyle to dash style string."""
    mapping = {
        "-": "solid",
        "--": "dash",
        ":": "dot",
        "-.": "dashdot",
        "solid": "solid",
        "dashed": "dash",
        "dotted": "dot",
        "dashdot": "dashdot",
    }
    return mapping.get(ls, "solid")


def map_marker(marker: str) -> str:
    """Map Matplotlib marker style to symbol string."""
    mapping = {
        "o": "circle",
        "s": "square",
        "D": "diamond",
        "^": "triangle-up",
        "x": "x",
        "+": "cross",
        "*": "star",
    }
    return mapping.get(marker, "circle")


def extract_lines(ax: Any) -> List[Dict[str, Any]]:
    """Extract Line2D artists from Axes into trace dicts."""
    traces = []
    for line in ax.lines:
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        if hasattr(xdata, "tolist"):
            xdata = xdata.tolist()
        if hasattr(ydata, "tolist"):
            ydata = ydata.tolist()

        color = rgba_to_hex_or_rgb(line.get_color())
        linewidth = float(f"{line.get_linewidth():g}")
        linestyle = map_linestyle(line.get_linestyle())
        marker_style = line.get_marker()

        mode = "lines"
        if marker_style and marker_style not in ("None", "none", "", " "):
            mode = "lines+markers" if linestyle != "none" else "markers"

        trace = {
            "type": "scatter",
            "x": xdata,
            "y": ydata,
            "mode": mode,
            "name": line.get_label() if not line.get_label().startswith("_") else None,
            "line": {
                "color": color,
                "width": linewidth,
                "dash": linestyle,
            },
        }

        if "markers" in mode and marker_style:
            trace["marker"] = {
                "symbol": map_marker(marker_style),
                "size": line.get_markersize(),
                "color": color,
            }

        traces.append(trace)
    return traces


def extract_collections(ax: Any) -> List[Dict[str, Any]]:
    """Extract collections (scatter PathCollections, QuadMesh heatmaps, etc.) into trace dicts."""
    traces = []
    for collection in ax.collections:
        # PathCollection -> Scatter
        if isinstance(collection, mcoll.PathCollection):
            offsets = collection.get_offsets()
            if len(offsets) > 0:
                xdata = offsets[:, 0].tolist()
                ydata = offsets[:, 1].tolist()
                fc = collection.get_facecolors()
                color = rgba_to_hex_or_rgb(fc[0]) if len(fc) > 0 else "#1f77b4"
                sizes = collection.get_sizes()
                size = float(np.sqrt(sizes[0])) if len(sizes) > 0 else 6.0

                label = collection.get_label()
                trace = {
                    "type": "scatter",
                    "x": xdata,
                    "y": ydata,
                    "mode": "markers",
                    "name": label if label and not label.startswith("_") else None,
                    "marker": {
                        "color": color,
                        "size": size,
                    },
                }
                traces.append(trace)

        # QuadMesh -> Heatmap
        elif isinstance(collection, mcoll.QuadMesh):
            array = collection.get_array()
            if array is not None:
                shape = collection._meshWidth, collection._meshHeight
                grid_z = array.reshape(shape[1], shape[0]).tolist() if hasattr(array, "reshape") else array.tolist()
                trace = {
                    "type": "heatmap",
                    "z": grid_z,
                    "name": collection.get_label() if not str(collection.get_label()).startswith("_") else None,
                }
                traces.append(trace)

    return traces


def extract_layout(ax: Any) -> Dict[str, Any]:
    """Extract axis titles, limits, log scale, and grid settings into a layout dict."""
    layout = {}

    title = ax.get_title()
    if title:
        layout["title"] = {"text": title}

    xlabel = ax.get_xlabel()
    xlim = ax.get_xlim()
    layout["xaxis"] = {
        "title": {"text": xlabel} if xlabel else None,
        "range": list(xlim) if xlim else None,
        "type": "log" if ax.get_xscale() == "log" else "linear",
    }

    ylabel = ax.get_ylabel()
    ylim = ax.get_ylim()
    layout["yaxis"] = {
        "title": {"text": ylabel} if ylabel else None,
        "range": list(ylim) if ylim else None,
        "type": "log" if ax.get_yscale() == "log" else "linear",
    }

    # Grid check
    xgrid = any(line.get_visible() for line in ax.xaxis.get_gridlines())
    ygrid = any(line.get_visible() for line in ax.yaxis.get_gridlines())
    if xgrid:
        layout["xaxis"]["showgrid"] = True
    if ygrid:
        layout["yaxis"]["showgrid"] = True

    return layout
