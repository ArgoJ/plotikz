"""Extraction and formatting of Plotly layout shapes into TikZ draw commands."""

import re
from typing import Dict, Any, List, Optional
from ..utils import clean_val, format_color, format_coord_val
from .subplots import normalize_axis_key


def format_point(x: Any, y: Any, xref: str = "x", yref: str = "y") -> str:
    """Format coordinate point according to reference axes (paper vs data cs)."""
    x_clean = clean_val(x)
    y_clean = clean_val(y)
    x_str = format_coord_val(x_clean)
    y_str = format_coord_val(y_clean)

    xref_str = str(xref or "x").lower()
    yref_str = str(yref or "y").lower()

    is_x_paper = "paper" in xref_str
    is_y_paper = "paper" in yref_str

    if is_x_paper and is_y_paper:
        return f"(rel axis cs:{x_str}, {y_str})"
    elif is_x_paper:
        return f"({{rel axis cs:{x_str},0}} |- {{axis cs:0,{y_str}}})"
    elif is_y_paper:
        return f"({{axis cs:{x_str},0}} |- {{rel axis cs:0,{y_str}}})"
    else:
        return f"(axis cs:{x_str}, {y_str})"


def parse_svg_path_to_tikz(path_str: str, xref: str = "x", yref: str = "y") -> Optional[str]:
    """Parse SVG path commands (M, L, H, V, C, Q, Z) into TikZ path sequence."""
    if not path_str or not isinstance(path_str, str):
        return None

    # Tokenize letters and numbers (including floating points & exponentials)
    matches = re.findall(r"([A-Za-z])|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)", path_str)
    raw_tokens: List[Any] = []
    for letter, num in matches:
        if letter:
            raw_tokens.append(letter)
        elif num:
            try:
                raw_tokens.append(float(num))
            except ValueError:
                pass

    if not raw_tokens:
        return None

    cmd = None
    curr_x, curr_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    parts = []

    idx = 0
    n = len(raw_tokens)
    while idx < n:
        item = raw_tokens[idx]
        if isinstance(item, str):
            cmd = item
            idx += 1

        if cmd in ("M", "m"):
            if idx + 1 < n and isinstance(raw_tokens[idx], (int, float)) and isinstance(raw_tokens[idx + 1], (int, float)):
                x, y = float(raw_tokens[idx]), float(raw_tokens[idx + 1])
                idx += 2
                if cmd == "m":
                    x += curr_x
                    y += curr_y
                curr_x, curr_y = x, y
                start_x, start_y = x, y
                parts.append(format_point(x, y, xref, yref))
                cmd = "L" if cmd == "M" else "l"
            else:
                idx += 1

        elif cmd in ("L", "l"):
            if idx + 1 < n and isinstance(raw_tokens[idx], (int, float)) and isinstance(raw_tokens[idx + 1], (int, float)):
                x, y = float(raw_tokens[idx]), float(raw_tokens[idx + 1])
                idx += 2
                if cmd == "l":
                    x += curr_x
                    y += curr_y
                curr_x, curr_y = x, y
                parts.append(f"-- {format_point(x, y, xref, yref)}")
            else:
                idx += 1

        elif cmd in ("H", "h"):
            if idx < n and isinstance(raw_tokens[idx], (int, float)):
                x = float(raw_tokens[idx])
                idx += 1
                if cmd == "h":
                    x += curr_x
                curr_x = x
                parts.append(f"-- {format_point(curr_x, curr_y, xref, yref)}")
            else:
                idx += 1

        elif cmd in ("V", "v"):
            if idx < n and isinstance(raw_tokens[idx], (int, float)):
                y = float(raw_tokens[idx])
                idx += 1
                if cmd == "v":
                    y += curr_y
                curr_y = y
                parts.append(f"-- {format_point(curr_x, curr_y, xref, yref)}")
            else:
                idx += 1

        elif cmd in ("C", "c"):
            if idx + 5 < n and all(isinstance(raw_tokens[idx + k], (int, float)) for k in range(6)):
                x1, y1, x2, y2, x, y = [float(raw_tokens[idx + k]) for k in range(6)]
                idx += 6
                if cmd == "c":
                    x1 += curr_x
                    y1 += curr_y
                    x2 += curr_x
                    y2 += curr_y
                    x += curr_x
                    y += curr_y
                curr_x, curr_y = x, y
                p1 = format_point(x1, y1, xref, yref)
                p2 = format_point(x2, y2, xref, yref)
                pe = format_point(x, y, xref, yref)
                parts.append(f".. controls {p1} and {p2} .. {pe}")
            else:
                idx += 1

        elif cmd in ("Q", "q"):
            if idx + 3 < n and all(isinstance(raw_tokens[idx + k], (int, float)) for k in range(4)):
                x1, y1, x, y = [float(raw_tokens[idx + k]) for k in range(4)]
                idx += 4
                if cmd == "q":
                    x1 += curr_x
                    y1 += curr_y
                    x += curr_x
                    y += curr_y
                curr_x, curr_y = x, y
                p1 = format_point(x1, y1, xref, yref)
                pe = format_point(x, y, xref, yref)
                parts.append(f".. controls {p1} .. {pe}")
            else:
                idx += 1

        elif cmd in ("Z", "z"):
            parts.append("-- cycle")
            curr_x, curr_y = start_x, start_y
            idx += 1
        else:
            idx += 1

    return " ".join(parts) if parts else None


def format_shape_to_tikz(shape: Dict[str, Any]) -> Optional[str]:
    """Format single Plotly shape dictionary into a TikZ \\draw command."""
    shape_type = shape.get("type", "rect")
    xref = str(shape.get("xref", "x"))
    yref = str(shape.get("yref", "y"))
    opacity = shape.get("opacity")

    fillcolor = shape.get("fillcolor")
    line = shape.get("line") or {}

    style_opts: List[str] = []

    # Fill options
    if fillcolor and str(fillcolor).lower() != "transparent":
        col_opt, col_opacity = format_color(str(fillcolor))
        if col_opt:
            style_opts.append(col_opt.replace("color=", "fill="))

        fill_op = None
        if opacity is not None and isinstance(opacity, (int, float)):
            fill_op = float(opacity)
            if col_opacity is not None:
                fill_op *= col_opacity
        elif col_opacity is not None:
            fill_op = col_opacity

        if fill_op is not None and fill_op < 1.0:
            style_opts.append(f"fill opacity={fill_op:g}")

    # Draw / Stroke options
    line_color = line.get("color")
    line_width = line.get("width")
    line_dash = line.get("dash")

    if line_width == 0 or (line_color and str(line_color).lower() == "transparent"):
        style_opts.append("draw=none")
    elif line_color:
        col_opt, col_opacity = format_color(str(line_color))
        if col_opt:
            style_opts.append(col_opt.replace("color=", "draw="))

        draw_op = None
        if opacity is not None and isinstance(opacity, (int, float)):
            draw_op = float(opacity)
            if col_opacity is not None:
                draw_op *= col_opacity
        elif col_opacity is not None:
            draw_op = col_opacity

        if draw_op is not None and draw_op < 1.0:
            style_opts.append(f"draw opacity={draw_op:g}")

        if line_width is not None and isinstance(line_width, (int, float)) and line_width > 0:
            style_opts.append(f"line width={line_width:g}pt")
    elif line:
        if line_width is not None and isinstance(line_width, (int, float)):
            if line_width > 0:
                style_opts.append(f"line width={line_width:g}pt")
            else:
                style_opts.append("draw=none")

    if line_dash:
        dash_map = {
            "solid": None,
            "dash": "dashed",
            "dot": "dotted",
            "dashdot": "dash dot",
            "longdash": "dash pattern=on 6pt off 2pt",
            "longdashdot": "dash pattern=on 6pt off 2pt on 1pt off 2pt",
        }
        d_opt = dash_map.get(str(line_dash).lower())
        if d_opt:
            style_opts.append(d_opt)

    opts_str = f"[{', '.join(style_opts)}]" if style_opts else ""

    # Geometries
    if shape_type == "rect":
        x0 = shape.get("x0", 0)
        x1 = shape.get("x1", 1)
        y0 = shape.get("y0", 0)
        y1 = shape.get("y1", 1)
        p0 = format_point(x0, y0, xref, yref)
        p1 = format_point(x1, y1, xref, yref)
        return f"\\draw{opts_str} {p0} rectangle {p1};"

    elif shape_type == "line":
        x0 = shape.get("x0", 0)
        x1 = shape.get("x1", 1)
        y0 = shape.get("y0", 0)
        y1 = shape.get("y1", 1)
        p0 = format_point(x0, y0, xref, yref)
        p1 = format_point(x1, y1, xref, yref)
        return f"\\draw{opts_str} {p0} -- {p1};"

    elif shape_type == "circle":
        x0_v = clean_val(shape.get("x0", 0))
        x1_v = clean_val(shape.get("x1", 1))
        y0_v = clean_val(shape.get("y0", 0))
        y1_v = clean_val(shape.get("y1", 1))

        x0_f = float(x0_v) if x0_v is not None else 0.0
        x1_f = float(x1_v) if x1_v is not None else 1.0
        y0_f = float(y0_v) if y0_v is not None else 0.0
        y1_f = float(y1_v) if y1_v is not None else 1.0

        cx = (x0_f + x1_f) / 2.0
        cy = (y0_f + y1_f) / 2.0
        rx = abs(x1_f - x0_f) / 2.0
        ry = abs(y1_f - y0_f) / 2.0

        center_pt = format_point(cx, cy, xref, yref)
        rx_str = format_coord_val(rx)
        ry_str = format_coord_val(ry)
        return f"\\draw{opts_str} {center_pt} circle [x radius={rx_str}, y radius={ry_str}];"

    elif shape_type == "path":
        path_str = shape.get("path")
        if path_str:
            tikz_path = parse_svg_path_to_tikz(path_str, xref, yref)
            if tikz_path:
                return f"\\draw{opts_str} {tikz_path};"

    return None


def extract_shapes(layout_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse layout shapes into formatted TikZ draw entry dicts."""
    shapes_list = []
    raw_shapes = layout_data.get("shapes", [])
    if not isinstance(raw_shapes, (list, tuple)):
        return shapes_list

    for shape in raw_shapes:
        if not isinstance(shape, dict):
            continue

        shape_code = format_shape_to_tikz(shape)
        if shape_code:
            layer = shape.get("layer", "below")
            if layer not in ("below", "above"):
                layer = "below"
            shapes_list.append({
                "code": shape_code,
                "layer": layer,
                "x_key": normalize_axis_key(shape.get("xref", "x"), "x"),
                "y_key": normalize_axis_key(shape.get("yref", "y"), "y"),
            })

    return shapes_list
