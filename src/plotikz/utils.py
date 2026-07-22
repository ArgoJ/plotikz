"""Utility helper functions for plotikz formatting and escaping."""

import math
import re
from typing import Any, Tuple, Optional


def format_color(color_str: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Parse Plotly color string (hex, rgb, rgba, named) and return
    (tikz_color_option, opacity).
    """
    if not color_str or not isinstance(color_str, str):
        return None, None

    color_str = color_str.strip()

    # Hex color #RRGGBB or #RGB
    if color_str.startswith("#"):
        hex_val = color_str.lstrip("#")
        if len(hex_val) == 3:
            hex_val = "".join([c * 2 for c in hex_val])
        if len(hex_val) == 6:
            try:
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
                return f"color={{rgb,255:red,{r};green,{g};blue,{b}}}", None
            except ValueError:
                pass

    # rgba(r, g, b, a) or rgb(r, g, b)
    rgba_match = re.match(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)",
        color_str,
        re.IGNORECASE,
    )
    if rgba_match:
        r, g, b, a = rgba_match.groups()
        color_opt = f"color={{rgb,255:red,{r};green,{g};blue,{b}}}"
        opacity = float(a) if a is not None else None
        return color_opt, opacity

    # Named or standard color
    return f"color={color_str}", None


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
