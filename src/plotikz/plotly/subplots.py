"""Subplot detection, axis normalization, and axis block construction."""

import re
from typing import Dict, Any, List, Tuple, Optional
from ..utils import clean_val, get_nice_ticks
from .heatmap_contour import _to_list
from .options_builder import build_axis_options


def normalize_axis_key(k: Any, axis_type: str = "y") -> str:
    """Normalize axis names ('y', 'y1', 'yaxis1' -> 'yaxis', 'y2' -> 'yaxis2')."""
    if not k:
        return f"{axis_type}axis"
    s = str(k).lower()
    if s in (axis_type, f"{axis_type}1", f"{axis_type}axis", f"{axis_type}axis1"):
        return f"{axis_type}axis"
    m = re.search(r"\d+", s)
    if m:
        return f"{axis_type}axis{m.group(0)}"
    return f"{axis_type}axis"


def detect_subplots(
    processed_traces: List[Dict[str, Any]], layout_data: Dict[str, Any]
) -> Tuple[Dict[Tuple[str, str], List[Dict[str, Any]]], bool]:
    """Group traces into subplots and check if x-axes are shared."""
    subplot_groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

    for t_info in processed_traces:
        raw_t = t_info.get("raw_trace", {})
        x_key = normalize_axis_key(raw_t.get("xaxis", "x"), "x")
        y_key = normalize_axis_key(raw_t.get("yaxis", "y"), "y")
        sp_key = (x_key, y_key)
        if sp_key not in subplot_groups:
            subplot_groups[sp_key] = []
        subplot_groups[sp_key].append(t_info)

    # Determine if x-axes are shared across subplots
    is_shared_x = len(subplot_groups) > 1
    if is_shared_x:
        matches_x = any(
            isinstance(layout_data.get(k), dict) and layout_data[k].get("matches") in ("x", "xaxis")
            for k in layout_data if k.startswith("xaxis") and k != "xaxis"
        )
        if not matches_x:
            x_keys = {key[0] for key in subplot_groups.keys()}
            is_shared_x = (len(x_keys) == 1) or len(subplot_groups) > 1

    return subplot_groups, is_shared_x


def compute_global_x_bounds(processed_traces: List[Dict[str, Any]]) -> Tuple[Optional[float], Optional[float]]:
    """Calculate overall min and max x-values across all traces."""
    all_x_vals = []
    for t_info in processed_traces:
        raw_t = t_info.get("raw_trace", {})
        rx = _to_list(raw_t.get("x", []))
        for v in rx:
            cv = clean_val(v)
            if cv is not None and isinstance(cv, (int, float)):
                all_x_vals.append(float(cv))

    if all_x_vals:
        return min(all_x_vals), max(all_x_vals)
    return None, None


def match_subplot_title(raw_annotations: Any, y_key: str, sp_idx: int) -> Optional[str]:
    """Match subplot title from layout annotations by yref position."""
    if isinstance(raw_annotations, (list, tuple)):
        y_num = y_key.replace("yaxis", "")
        target_yref = f"y{y_num} domain" if y_num else "y domain"
        for ann in raw_annotations:
            if isinstance(ann, dict) and (
                ann.get("yref") == target_yref or ann.get("yref") == f"y{sp_idx} domain"
            ):
                return ann.get("text")
    return None


def apply_shared_x_options(
    opts: List[str], x_min: float, x_max: float, is_bottom: bool
) -> List[str]:
    """Apply shared x-axis limits and tick marks to a subplot."""
    nice_ticks = get_nice_ticks(x_min, x_max, max_ticks=5)
    ticks_str = ",".join([f"{v:g}" for v in nice_ticks])

    clean_opts = [
        opt for opt in opts
        if not (opt.startswith("xmin=") or opt.startswith("xmax=") or opt.startswith("xtick="))
    ]
    clean_opts.append(f"xmin={x_min:g}")
    clean_opts.append(f"xmax={x_max:g}")
    clean_opts.append(f"xtick={{{ticks_str}}}")

    if not is_bottom:
        clean_opts = [opt for opt in clean_opts if not opt.startswith("xlabel=")]
        clean_opts.append("xticklabels=\\empty")

    return clean_opts


def build_axis_blocks(
    subplot_groups: Dict[Tuple[str, str], List[Dict[str, Any]]],
    is_shared_x: bool,
    layout_data: Dict[str, Any],
    processed_traces: List[Dict[str, Any]],
    **kwargs,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Build axis options and layout structures for single-plot or multi-subplot figures."""
    if len(subplot_groups) <= 1:
        master_opts = build_axis_options(layout_data, processed_traces, **kwargs)
        return [], master_opts

    axis_blocks = []
    num_sp = len(subplot_groups)
    raw_annotations = layout_data.get("annotations", [])

    global_x_min, global_x_max = compute_global_x_bounds(processed_traces) if is_shared_x else (None, None)

    # Subplot height sizing
    if layout_data.get("height") and isinstance(layout_data["height"], (int, float)):
        h_total_cm = float(layout_data["height"]) / 50.0
        h_per_sp = max(3.2, round((h_total_cm / num_sp) - 0.6, 1))
    else:
        h_per_sp = 4.0

    sp_idx = 0
    for (x_key, y_key), sp_traces in subplot_groups.items():
        sp_idx += 1
        is_bottom = (sp_idx == num_sp)

        sub_layout = dict(layout_data)
        sub_layout["xaxis"] = dict(layout_data.get(x_key) or layout_data.get("xaxis") or {})
        sub_layout["yaxis"] = dict(layout_data.get(y_key) or layout_data.get("yaxis") or {})

        sp_title = match_subplot_title(raw_annotations, y_key, sp_idx)
        if sp_title:
            sub_layout["title"] = sp_title
        elif sp_idx > 1 and "title" in sub_layout:
            sub_layout.pop("title", None)

        raw_sp_traces = [t.get("raw_trace", {}) for t in sp_traces]
        sp_opts = build_axis_options(sub_layout, raw_sp_traces, **kwargs)

        if is_shared_x and global_x_min is not None and global_x_max is not None:
            sp_opts = apply_shared_x_options(sp_opts, global_x_min, global_x_max, is_bottom)

        # Height and width
        sp_opts = [opt for opt in sp_opts if not opt.startswith("height=")]
        sp_opts.append(f"height={h_per_sp:g}cm")
        if not any("width=" in opt for opt in sp_opts):
            sp_opts.append("width=14cm")

        # Position
        name = f"plot{sp_idx}"
        sp_opts.insert(0, f"name={name}")
        if sp_idx > 1:
            prev_name = f"plot{sp_idx - 1}"
            sp_opts.append(f"at={{({prev_name}.below south west)}}")
            sp_opts.append("anchor=north west")
            sp_opts.append("yshift=-0.8cm")

        axis_blocks.append({
            "axis_options": sp_opts,
            "axis_options_formatted": ",\n    ".join(sp_opts),
            "traces": sp_traces,
            "annotations": [],
        })

    return axis_blocks, []
