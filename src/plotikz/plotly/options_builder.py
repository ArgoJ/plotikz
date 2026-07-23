"""PGFPlots axis options building for layout, bar, parcoords, and generic plots."""

from typing import Dict, Any, List
from ..utils import escape_tex, clean_val
from .heatmap_contour import build_heatmap_contour_options, _to_list


def build_axis_options(layout: Dict[str, Any], traces: List[Dict[str, Any]]) -> List[str]:
    """Build list of PGFPlots axis options based on layout and trace types."""
    options = build_basic_layout_options(layout)

    trace_types = set()
    for t in traces:
        if isinstance(t, dict):
            ttype = t.get("type") or (t.get("raw_trace") or {}).get("type", "scatter")
            trace_types.add(ttype)

    if "heatmap" in trace_types or "contour" in trace_types:
        build_heatmap_contour_options(options, traces)
    elif "bar" in trace_types:
        build_bar_options(options, traces)
    elif "parcoords" in trace_types:
        build_parcoords_options(options, traces)

    return options


def build_basic_layout_options(layout: Dict[str, Any]) -> List[str]:
    """Extract title, axes, layout dimensions, and legend options."""
    options = []

    # Title
    title = layout.get("title")
    title_text = title.get("text", "") if isinstance(title, dict) else (str(title) if title is not None else "")
    if title_text:
        options.append(f"title={{{escape_tex(title_text)}}}")

    # X & Y Axes
    options.extend(extract_single_axis_options(layout.get("xaxis") or {}, "x"))
    options.extend(extract_single_axis_options(layout.get("yaxis") or {}, "y"))

    # Dimensions & Legend
    width = layout.get("width")
    height = layout.get("height")
    if width and isinstance(width, (int, float)):
        options.append(f"width={width / 50.0:.1f}cm")
    if height and isinstance(height, (int, float)):
        options.append(f"height={height / 50.0:.1f}cm")
    if layout.get("showlegend") is False:
        options.append("legend pos=none")

    return options


def extract_single_axis_options(axis_dict: Dict[str, Any], axis_name: str) -> List[str]:
    """Extract title, log mode, range, and grid line settings for x or y axis."""
    opts = []
    prefix = "x" if axis_name == "x" else "y"

    title = axis_dict.get("title")
    title_text = title.get("text", "") if isinstance(title, dict) else (str(title) if title is not None else "")
    if title_text:
        opts.append(f"{prefix}label={{{escape_tex(title_text)}}}")

    if axis_dict.get("type") == "log":
        opts.append(f"{prefix}mode=log")

    axis_range = axis_dict.get("range")
    if axis_range and isinstance(axis_range, (list, tuple)) and len(axis_range) == 2:
        opts.append(f"{prefix}min={axis_range[0]}")
        opts.append(f"{prefix}max={axis_range[1]}")

    if axis_dict.get("showgrid") is True:
        opts.append(f"{prefix}majorgrids=true")
    elif axis_dict.get("showgrid") is False:
        opts.append(f"{prefix}majorgrids=false")

    return opts


def build_bar_options(options: List[str], traces: List[Dict[str, Any]]) -> None:
    """Add PGFPlots options for Bar charts."""
    if not any("ybar" in opt or "xbar" in opt for opt in options):
        options.append("ybar")
    if not any("ymin=" in opt for opt in options):
        options.append("ymin=0")

    for t in traces:
        raw_t = t.get("raw_trace") or t
        if isinstance(raw_t, dict) and raw_t.get("type") == "bar":
            raw_x = _to_list(raw_t.get("x", []))
            if raw_x and not any("xtick=" in opt for opt in options):
                clean_ticks = []
                for v in raw_x:
                    cv = clean_val(v)
                    if cv is not None:
                        clean_ticks.append(f"{cv:g}" if isinstance(cv, (int, float)) else f"{{{cv}}}")
                if clean_ticks:
                    options.append(f"xtick={{{','.join(clean_ticks)}}}")
            break


def build_parcoords_options(options: List[str], traces: List[Dict[str, Any]]) -> None:
    """Add PGFPlots options for Parallel Coordinates plots."""
    options.append("xmajorgrids=true")
    options.append("grid style={solid, black!60, line width=0.8pt}")
    options.append("xticklabel style={rotate=30, anchor=north east, font=\\small}")

    if not any("ymin=" in opt for opt in options):
        options.append("ymin=0")
    if not any("ymax=" in opt for opt in options):
        options.append("ymax=1")

    for t in traces:
        raw_t = t.get("raw_trace") or t
        if isinstance(raw_t, dict) and raw_t.get("type") == "parcoords":
            dimensions = raw_t.get("dimensions", [])
            if dimensions and isinstance(dimensions, list):
                labels = []
                ticks = []
                for idx, dim in enumerate(dimensions, start=1):
                    ticks.append(str(idx))
                    if isinstance(dim, dict):
                        labels.append(f"{{{escape_tex(str(dim.get('label', f'Dim {idx}')))}}}")
                    else:
                        labels.append(f"{{{f'Dim {idx}'}}}")

                if ticks and not any(opt.startswith("xtick=") for opt in options):
                    options.append(f"xtick={{{','.join(ticks)}}}")
                    options.append(f"xticklabels={{{','.join(labels)}}}")

                if not any("xmin=" in opt for opt in options):
                    options.append("xmin=1")
                if not any("xmax=" in opt for opt in options):
                    options.append(f"xmax={len(dimensions)}")
                if not any("enlargelimits=" in opt for opt in options):
                    options.append("enlargelimits=false")
            break
