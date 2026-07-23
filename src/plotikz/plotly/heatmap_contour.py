"""Heatmap and Contour specific PGFPlots options and bounds calculation."""

import numpy as np
from typing import Dict, Any, List

from ..utils import clean_val, get_nice_ticks, format_colorscale, escape_tex


def _to_list(val: Any) -> List[Any]:
    """Safely convert numpy arrays, pandas series, or iterables into a standard Python list."""
    if hasattr(val, "tolist") and callable(getattr(val, "tolist", None)):
        return val.tolist()
    if hasattr(val, "values") and not isinstance(val, dict):
        vals = getattr(val, "values")
        return vals if not callable(vals) else list(vals)
    if isinstance(val, (list, tuple)):
        return list(val)
    return []


def extract_z_values(raw_z: Any) -> List[float]:
    """Recursively extract all numeric values from a 1D, 2D, or nested z matrix/list."""
    raw_list = _to_list(raw_z)
    z_vals = []
    if raw_list:
        def _flatten(item):
            if isinstance(item, list):
                for sub in item:
                    _flatten(sub)
            else:
                cv = clean_val(item)
                if cv is not None and isinstance(cv, (int, float)) and not (isinstance(cv, float) and np.isnan(cv)):
                    z_vals.append(float(cv))
        _flatten(raw_list)
    return z_vals


def build_heatmap_contour_options(
    options: List[str], traces: List[Dict[str, Any]], **kwargs
) -> None:
    """Add PGFPlots options for Heatmap and Contour plots."""
    colorbar_ticks = kwargs.get("colorbar_ticks", 5)
    if not any("view=" in opt for opt in options):
        options.append("view={0}{90}")
    if not any("colorbar" in opt for opt in options):
        options.append("colorbar")
    if not any("enlargelimits" in opt for opt in options):
        options.append("enlargelimits=false")
    if not any("axis on top" in opt for opt in options):
        options.append("axis on top")

    for t in traces:
        raw_t = t.get("raw_trace") or t
        t_type = raw_t.get("type") or t.get("type")
        if not isinstance(raw_t, dict) or t_type not in ("heatmap", "contour"):
            continue

        # Skip constraint contours (e.g. ROA boundary) when configuring colorbar range
        contours_cfg = raw_t.get("contours", {})
        if t_type == "contour" and contours_cfg.get("type") == "constraint":
            continue

        z_vals = extract_z_values(raw_t.get("z", []))

        if z_vals:
            z_min = raw_t.get("zmin") if raw_t.get("zmin") is not None else min(z_vals)
            z_max = raw_t.get("zmax") if raw_t.get("zmax") is not None else max(z_vals)
            if not any("point meta min" in opt for opt in options):
                options.append(f"point meta min={z_min:g}")
            if not any("point meta max" in opt for opt in options):
                options.append(f"point meta max={z_max:g}")

            if not any("colorbar style" in opt for opt in options):
                ticks_nice = get_nice_ticks(z_min, z_max, max_ticks=max(1, colorbar_ticks))
                ticks_str = ",".join([f"{v:g}" for v in ticks_nice])
                options.append(f"colorbar style={{ytick={{{ticks_str}}}}}")

        if t_type == "heatmap":
            raw_z = _to_list(raw_t.get("z", []))
            add_heatmap_halfcell_bounds(options, raw_t, raw_z)

        cs_val = raw_t.get("colorscale")
        cm_opt, _ = format_colorscale(cs_val)
        if cm_opt and not any("colormap" in opt for opt in options):
            options.append(cm_opt)
        break


def add_heatmap_halfcell_bounds(options: List[str], t: Dict[str, Any], raw_z: List[Any]) -> None:
    """Calculate half-cell boundaries so matrix plot fills axis frame 100% without clipping outer cells."""
    raw_x = _to_list(t.get("x"))
    raw_y = _to_list(t.get("y"))

    num_rows = len(raw_z) if raw_z and isinstance(raw_z, list) else 1
    first_row = _to_list(raw_z[0]) if (raw_z and isinstance(raw_z, list)) else []
    num_cols = len(first_row) if isinstance(first_row, list) and first_row else 1

    is_x_num = bool(raw_x and all(isinstance(clean_val(v), (int, float)) for v in raw_x))
    is_y_num = bool(raw_y and all(isinstance(clean_val(v), (int, float)) for v in raw_y))

    # X-Axis half-cell bounds
    if not any(opt.startswith("xmin=") for opt in options) or not any(opt.startswith("xmax=") for opt in options):
        if is_x_num:
            dx = (float(raw_x[-1]) - float(raw_x[0])) / max(1, len(raw_x) - 1) if len(raw_x) > 1 else 1.0
            half_dx = dx / 2.0
            if not any("xmin=" in opt for opt in options):
                options.append(f"xmin={float(raw_x[0]) - half_dx:g}")
            if not any("xmax=" in opt for opt in options):
                options.append(f"xmax={float(raw_x[-1]) + half_dx:g}")
        else:
            if not any("xmin=" in opt for opt in options):
                options.append("xmin=0.5")
            if not any("xmax=" in opt for opt in options):
                options.append(f"xmax={num_cols + 0.5:g}")

    if not any(opt.startswith("xtick=") for opt in options):
        if is_x_num:
            xticks_str = ",".join([f"{clean_val(v):g}" for v in raw_x])
        elif raw_x:
            ticks = [str(i + 1) for i in range(len(raw_x))]
            labels = [escape_tex(str(v)) for v in raw_x]
            xticks_str = ",".join(ticks)
            options.append(f"xticklabels={{{','.join(labels)}}}")
        else:
            xticks_str = ",".join([str(i + 1) for i in range(num_cols)])
        options.append(f"xtick={{{xticks_str}}}")

    # Y-Axis half-cell bounds
    if not any(opt.startswith("ymin=") for opt in options) or not any(opt.startswith("ymax=") for opt in options):
        if is_y_num:
            dy = (float(raw_y[-1]) - float(raw_y[0])) / max(1, len(raw_y) - 1) if len(raw_y) > 1 else 1.0
            half_dy = dy / 2.0
            if not any("ymin=" in opt for opt in options):
                options.append(f"ymin={float(raw_y[0]) - half_dy:g}")
            if not any("ymax=" in opt for opt in options):
                options.append(f"ymax={float(raw_y[-1]) + half_dy:g}")
        else:
            if not any("ymin=" in opt for opt in options):
                options.append("ymin=0.5")
            if not any("ymax=" in opt for opt in options):
                options.append(f"ymax={num_rows + 0.5:g}")

    if not any(opt.startswith("ytick=") for opt in options):
        if is_y_num:
            yticks_str = ",".join([f"{clean_val(v):g}" for v in raw_y])
        elif raw_y:
            ticks = [str(i + 1) for i in range(len(raw_y))]
            labels = [escape_tex(str(v)) for v in raw_y]
            yticks_str = ",".join(ticks)
            options.append(f"yticklabels={{{','.join(labels)}}}")
        else:
            yticks_str = ",".join([str(i + 1) for i in range(num_rows)])
        options.append(f"ytick={{{yticks_str}}}")
