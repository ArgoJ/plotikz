"""Handler for Scatter, Scattergl, Scatter3d traces."""

from typing import Dict, Any, Optional

from .base import TraceHandler
from ..utils import format_color, escape_tex, clean_val, format_coord_val


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
