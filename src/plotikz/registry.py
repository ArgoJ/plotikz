"""Trace handler registry and trace parsers for plotikz."""

import math
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Set, Optional


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


class TraceHandler(ABC):
    """Base class for Plotly trace conversion handlers."""

    def __init__(self):
        self.packages: Set[str] = set()
        self.libraries: Set[str] = set()

    @abstractmethod
    def can_handle(self, trace_type: str) -> bool:
        """Check if this handler supports trace_type."""
        pass

    @abstractmethod
    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process trace and return trace metadata dictionary."""
        pass


class ScatterHandler(TraceHandler):
    """Handler for Scatter, Scattergl, Scatter3d traces."""

    def can_handle(self, trace_type: str) -> bool:
        return trace_type in ("scatter", "scattergl", "scatter3d", "")

    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        options = []
        mode = trace.get("mode", "lines")
        if mode is None:
            mode = "lines"

        # Line styling
        line = trace.get("line") or {}
        line_dash = line.get("dash")
        dash_map = {
            "dash": "dashed",
            "dot": "dotted",
            "dashdot": "dashdotted",
            "solid": "solid",
            "longdash": "densely dashed",
            "longdashdot": "densely dashdotted",
        }
        if line_dash in dash_map:
            options.append(dash_map[line_dash])

        line_width = line.get("width")
        if line_width is not None and isinstance(line_width, (int, float)):
            options.append(f"line width={line_width}pt")

        # Color
        color_str = line.get("color") or (trace.get("marker") or {}).get("color")
        if isinstance(color_str, str):
            col_opt, opacity = format_color(color_str)
            if col_opt:
                options.append(col_opt)
            if opacity is not None and opacity < 1.0:
                options.append(f"opacity={opacity}")

        trace_opacity = trace.get("opacity")
        if trace_opacity is not None and isinstance(trace_opacity, (int, float)) and trace_opacity < 1.0:
            options.append(f"opacity={trace_opacity}")

        # Markers
        if "markers" not in mode:
            options.append("mark=none")
        else:
            if "lines" not in mode:
                options.append("only marks")
            marker = trace.get("marker") or {}
            symbol = marker.get("symbol", "circle")
            symbol_map = {
                "circle": "mark=*",
                "circle-open": "mark=o",
                "square": "mark=square*",
                "square-open": "mark=square",
                "diamond": "mark=diamond*",
                "diamond-open": "mark=diamond",
                "triangle-up": "mark=triangle*",
                "cross": "mark=x",
                "x": "mark=x",
                "star": "mark=asterisk",
            }
            if isinstance(symbol, str):
                base_sym = symbol.split("-")[0] if "-" in symbol else symbol
                options.append(symbol_map.get(symbol, symbol_map.get(base_sym, "mark=*")))
            else:
                options.append("mark=*")

            size = marker.get("size")
            if size is not None and isinstance(size, (int, float)):
                options.append(f"mark size={max(1.0, size / 2.0):g}pt")

        # Coordinates
        raw_x = trace.get("x", [])
        raw_y = trace.get("y", [])

        if hasattr(raw_x, "values"):
            raw_x = raw_x.values
        if hasattr(raw_x, "tolist"):
            raw_x = raw_x.tolist()

        if hasattr(raw_y, "values"):
            raw_y = raw_y.values
        if hasattr(raw_y, "tolist"):
            raw_y = raw_y.tolist()

        coords = []
        for xi, yi in zip(raw_x, raw_y):
            cx = clean_val(xi)
            cy = clean_val(yi)
            if cx is not None and cy is not None:
                coords.append((format_coord_val(cx), format_coord_val(cy)))

        n_points = len(coords)
        prefix = tsv_prefix or "data"

        if n_points > tsv_threshold:
            data_type = "tsv"
            tsv_filename = f"{prefix}_trace_{trace_index}.tsv"
            lines = ["x\ty"] + [f"{x}\t{y}" for x, y in coords]
            tsv_content = "\n".join(lines)
            inline_coords = ""
        else:
            data_type = "inline"
            tsv_filename = ""
            tsv_content = ""
            inline_coords = " ".join([f"({x}, {y})" for x, y in coords])

        name = trace.get("name")
        showlegend = trace.get("showlegend", True)
        legend_entry = escape_tex(name) if (name and showlegend is not False) else None

        return {
            "plot_cmd": r"\addplot+",
            "options": options,
            "options_str": ", ".join(options),
            "data_type": data_type,
            "inline_coords": inline_coords,
            "tsv_filename": tsv_filename,
            "tsv_content": tsv_content,
            "legend_entry": legend_entry,
            "packages": self.packages,
            "libraries": self.libraries,
            "x_col": "x",
            "y_col": "y",
        }


class BarHandler(TraceHandler):
    """Handler for Bar traces."""

    def can_handle(self, trace_type: str) -> bool:
        return trace_type == "bar"

    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        options = ["ybar"]
        orientation = trace.get("orientation", "v")
        if orientation == "h":
            options = ["xbar"]

        marker = trace.get("marker") or {}
        color_str = marker.get("color")
        if isinstance(color_str, str):
            col_opt, opacity = format_color(color_str)
            if col_opt:
                fill_opt = col_opt.replace("color=", "fill=")
                options.append(fill_opt)
            if opacity is not None and opacity < 1.0:
                options.append(f"fill opacity={opacity}")

        raw_x = trace.get("x", [])
        raw_y = trace.get("y", [])

        if hasattr(raw_x, "tolist"):
            raw_x = raw_x.tolist()
        if hasattr(raw_y, "tolist"):
            raw_y = raw_y.tolist()

        coords = []
        for xi, yi in zip(raw_x, raw_y):
            cx = clean_val(xi)
            cy = clean_val(yi)
            if cx is not None and cy is not None:
                coords.append((format_coord_val(cx), format_coord_val(cy)))

        n_points = len(coords)
        prefix = tsv_prefix or "data"

        if n_points > tsv_threshold:
            data_type = "tsv"
            tsv_filename = f"{prefix}_trace_{trace_index}.tsv"
            lines = ["x\ty"] + [f"{x}\t{y}" for x, y in coords]
            tsv_content = "\n".join(lines)
            inline_coords = ""
        else:
            data_type = "inline"
            tsv_filename = ""
            tsv_content = ""
            inline_coords = " ".join([f"({x}, {y})" for x, y in coords])

        name = trace.get("name")
        showlegend = trace.get("showlegend", True)
        legend_entry = escape_tex(name) if (name and showlegend is not False) else None

        return {
            "plot_cmd": r"\addplot+",
            "options": options,
            "options_str": ", ".join(options),
            "data_type": data_type,
            "inline_coords": inline_coords,
            "tsv_filename": tsv_filename,
            "tsv_content": tsv_content,
            "legend_entry": legend_entry,
            "packages": self.packages,
            "libraries": self.libraries,
            "x_col": "x",
            "y_col": "y",
        }


class HeatmapHandler(TraceHandler):
    """Handler for Heatmap / Contour traces."""

    def __init__(self):
        super().__init__()
        self.libraries.add("colormaps")

    def can_handle(self, trace_type: str) -> bool:
        return trace_type in ("heatmap", "contour")

    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        options = ["matrix plot", "point meta=explicit"]
        raw_z = trace.get("z", [])
        raw_x = trace.get("x")
        raw_y = trace.get("y")

        coords = []
        if raw_z:
            if hasattr(raw_z, "tolist"):
                raw_z = raw_z.tolist()
            for r_idx, row in enumerate(raw_z):
                if hasattr(row, "tolist"):
                    row = row.tolist()
                y_val = raw_y[r_idx] if raw_y and r_idx < len(raw_y) else r_idx
                for c_idx, z_val in enumerate(row):
                    x_val = raw_x[c_idx] if raw_x and c_idx < len(raw_x) else c_idx
                    cz = clean_val(z_val)
                    if cz is not None:
                        coords.append((format_coord_val(x_val), format_coord_val(y_val), format_coord_val(cz)))

        n_points = len(coords)
        prefix = tsv_prefix or "data"

        if n_points > tsv_threshold:
            data_type = "tsv"
            tsv_filename = f"{prefix}_trace_{trace_index}.tsv"
            lines = ["x\ty\tz"] + [f"{x}\t{y}\t{z}" for x, y, z in coords]
            tsv_content = "\n".join(lines)
            inline_coords = ""
        else:
            data_type = "inline"
            tsv_filename = ""
            tsv_content = ""
            inline_coords = " ".join([f"({x}, {y}) [{z}]" for x, y, z in coords])

        name = trace.get("name")
        showlegend = trace.get("showlegend", False)
        legend_entry = escape_tex(name) if (name and showlegend) else None

        return {
            "plot_cmd": r"\addplot+",
            "options": options,
            "options_str": ", ".join(options),
            "data_type": data_type,
            "inline_coords": inline_coords,
            "tsv_filename": tsv_filename,
            "tsv_content": tsv_content,
            "legend_entry": legend_entry,
            "packages": self.packages,
            "libraries": self.libraries,
            "x_col": "x",
            "y_col": "y",
        }


class GenericHandler(TraceHandler):
    """Fallback handler for generic or unhandled trace types."""

    def can_handle(self, trace_type: str) -> bool:
        return True

    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        options = ["mark=none"]
        raw_x = trace.get("x", [])
        raw_y = trace.get("y", [])

        if hasattr(raw_x, "tolist"):
            raw_x = raw_x.tolist()
        if hasattr(raw_y, "tolist"):
            raw_y = raw_y.tolist()

        coords = []
        for xi, yi in zip(raw_x, raw_y):
            cx = clean_val(xi)
            cy = clean_val(yi)
            if cx is not None and cy is not None:
                coords.append((format_coord_val(cx), format_coord_val(cy)))

        n_points = len(coords)
        prefix = tsv_prefix or "data"

        if n_points > tsv_threshold:
            data_type = "tsv"
            tsv_filename = f"{prefix}_trace_{trace_index}.tsv"
            lines = ["x\ty"] + [f"{x}\t{y}" for x, y in coords]
            tsv_content = "\n".join(lines)
            inline_coords = ""
        else:
            data_type = "inline"
            tsv_filename = ""
            tsv_content = ""
            inline_coords = " ".join([f"({x}, {y})" for x, y in coords])

        name = trace.get("name")
        showlegend = trace.get("showlegend", True)
        legend_entry = escape_tex(name) if (name and showlegend is not False) else None

        return {
            "plot_cmd": r"\addplot+",
            "options": options,
            "options_str": ", ".join(options),
            "data_type": data_type,
            "inline_coords": inline_coords,
            "tsv_filename": tsv_filename,
            "tsv_content": tsv_content,
            "legend_entry": legend_entry,
            "packages": self.packages,
            "libraries": self.libraries,
            "x_col": "x",
            "y_col": "y",
        }


class TraceRegistry:
    """Registry for trace handlers."""

    def __init__(self):
        self._handlers: List[TraceHandler] = []

    def register(self, handler: TraceHandler):
        """Register a new trace handler."""
        self._handlers.append(handler)

    def get_handler(self, trace_type: str) -> TraceHandler:
        """Find handler for trace_type (searches in reverse order for overrides)."""
        for handler in reversed(self._handlers):
            if handler.can_handle(trace_type):
                return handler
        return GenericHandler()


# Default global registry pre-populated with standard handlers
default_registry = TraceRegistry()
default_registry.register(ScatterHandler())
default_registry.register(BarHandler())
default_registry.register(HeatmapHandler())
