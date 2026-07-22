"""Utility helper functions for plotikz formatting and escaping."""

import math
import re
from typing import Any, Tuple, Optional, List
import matplotlib.ticker as ticker


def get_nice_ticks(z_min: float, z_max: float, max_ticks: int = 5) -> List[float]:
    """Generate round, clean tick values within [z_min, z_max]."""
    try:
        locator = ticker.MaxNLocator(nbins=max_ticks, steps=[1, 2, 2.5, 5, 10])
        ticks = locator.tick_values(z_min, z_max)
        valid = [float(t) for t in ticks if z_min <= t <= z_max]
        if len(valid) >= 2:
            return valid
    except Exception:
        pass
    return [float(z_min), float(z_max)]


def format_color(color_str: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Parse Plotly color string (hex, rgb, rgba, hsl, hsla, named) and return
    (tikz_color_option, opacity).
    """
    if not color_str or not isinstance(color_str, str):
        return None, None

    color_str = color_str.strip()

    # Handle rgba(...) / rgb(...)
    rgba_match = re.match(
        r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)",
        color_str,
        re.IGNORECASE,
    )
    if rgba_match:
        r, g, b, a = rgba_match.groups()
        try:
            r_int, g_int, b_int = int(float(r)), int(float(g)), int(float(b))
            opacity = float(a) if a is not None else None
            return f"color={{rgb,255:red,{r_int};green,{g_int};blue,{b_int}}}", opacity
        except ValueError:
            pass

    # Handle hsla(...) / hsl(...)
    hsl_match = re.match(
        r"hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%(?:\s*,\s*([\d.]+))?\s*\)",
        color_str,
        re.IGNORECASE,
    )
    if hsl_match:
        h, s, l, a = hsl_match.groups()
        try:
            import colorsys
            r_f, g_f, b_f = colorsys.hls_to_rgb(float(h) / 360.0, float(l) / 100.0, float(s) / 100.0)
            r, g, b = int(round(r_f * 255)), int(round(g_f * 255)), int(round(b_f * 255))
            opacity = float(a) if a is not None else None
            return f"color={{rgb,255:red,{r};green,{g};blue,{b}}}", opacity
        except Exception:
            pass

    # Use matplotlib.colors.to_rgba for hex, named colors
    try:
        import matplotlib.colors as mcolors
        rgba = mcolors.to_rgba(color_str)
        r = int(round(rgba[0] * 255))
        g = int(round(rgba[1] * 255))
        b = int(round(rgba[2] * 255))
        opacity = rgba[3] if rgba[3] < 1.0 else None
        return f"color={{rgb,255:red,{r};green,{g};blue,{b}}}", opacity
    except Exception:
        pass

    return f"color={color_str}", None


def format_colorscale(colorscale: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse Plotly colorscale (named string or list of [stop, color] pairs)
    and return (pgfplots_option_string, colormap_name).
    """
    PLOTLY_DEFAULT_COLORSCALE = [
        [0.0, "#0d0887"],
        [0.1111111111111111, "#46039f"],
        [0.2222222222222222, "#7201a8"],
        [0.3333333333333333, "#9c179e"],
        [0.4444444444444444, "#bd3786"],
        [0.5555555555555556, "#d8576b"],
        [0.6666666666666666, "#ed7953"],
        [0.7777777777777778, "#fb9f3a"],
        [0.8888888888888888, "#fdca26"],
        [1.0, "#f0f921"],
    ]

    if not colorscale or colorscale == "plotly":
        colorscale = PLOTLY_DEFAULT_COLORSCALE

    if isinstance(colorscale, str):
        cs_lower = colorscale.lower()
        known_map = {
            "viridis": "colormap/viridis",
            "plasma": "colormap/plasma",
            "inferno": "colormap/inferno",
            "magma": "colormap/magma",
            "cividis": "colormap/cividis",
            "hot": "colormap/hot",
            "cool": "colormap/cool",
            "jet": "colormap/jet",
        }
        if cs_lower in known_map:
            return known_map[cs_lower], cs_lower
        return f"colormap/{cs_lower}", cs_lower

    if isinstance(colorscale, (list, tuple)):
        stops_str = []
        for stop in colorscale:
            if isinstance(stop, (list, tuple)) and len(stop) == 2:
                pos, col = stop
                try:
                    pct = int(round(float(pos) * 100))
                except (ValueError, TypeError):
                    pct = 0
                col_opt, _ = format_color(str(col))
                if col_opt and "color={rgb,255:red," in col_opt:
                    m = re.search(r"red,(\d+);green,(\d+);blue,(\d+)", col_opt)
                    if m:
                        r, g, b = m.groups()
                        stops_str.append(f"rgb255({pct})=({r},{g},{b})")
        if stops_str:
            cm_def = f"colormap={{plotly}}{{{' '.join(stops_str)}}}"
            return cm_def, "plotly"

    return None, None


def escape_tex(text: str) -> str:
    """Escape LaTeX special characters in text strings."""
    if not isinstance(text, str):
        return str(text)
    if "$" in text:  # Preserve LaTeX math blocks
        return text
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("_", r"\_"),
        ("%", r"\%"),
        ("&", r"\&"),
        ("#", r"\#"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def clean_val(val: Any) -> Optional[Any]:
    """Check if value is valid numeric or string (not None, nan, inf)."""
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
    if hasattr(val, "item"):
        val = val.item()
        if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
            return None
    return val


def format_coord_val(val: Any) -> str:
    """Format single coordinate value for TikZ output."""
    val = clean_val(val)
    if val is None:
        return "nan"
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return f"{val:g}"
    return str(val)
