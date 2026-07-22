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
        base_dir: Optional[str] = None,
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

        # Line shape (e.g. step plot 'hv', 'vh')
        line_shape = line.get("shape") or trace.get("line_shape")
        if line_shape in ("hv", "vh"):
            if line_shape == "hv":
                options.append("const plot")
            elif line_shape == "vh":
                options.append("const plot mark right")

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
                options.append(f"mark size={max(1.0, size / 2.5):g}pt")

            marker_color = (trace.get("marker") or {}).get("color") or color_str
            if isinstance(marker_color, str):
                mcol_opt, _ = format_color(marker_color)
                if mcol_opt:
                    m_color = mcol_opt.replace("color=", "")
                    options.append(f"mark options={{solid, fill={m_color}, draw={m_color}}}")
            else:
                options.append("mark options={solid}")

        # Coordinates
        raw_x = trace.get("x", [])
        raw_y = trace.get("y", [])

        if hasattr(raw_x, "tolist") and callable(getattr(raw_x, "tolist", None)):
            raw_x = raw_x.tolist()
        elif hasattr(raw_x, "values") and not isinstance(raw_x, dict):
            vals = getattr(raw_x, "values")
            raw_x = vals if not callable(vals) else list(vals)

        if hasattr(raw_y, "tolist") and callable(getattr(raw_y, "tolist", None)):
            raw_y = raw_y.tolist()
        elif hasattr(raw_y, "values") and not isinstance(raw_y, dict):
            vals = getattr(raw_y, "values")
            raw_y = vals if not callable(vals) else list(vals)

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
            table_content = ""
            inline_coords = ""
        else:
            data_type = "table_macro"
            tsv_filename = ""
            tsv_content = ""
            lines = ["x y"] + [f"{x} {y}" for x, y in coords]
            table_content = "\n".join(lines)
            inline_coords = " ".join([f"({x}, {y})" for x, y in coords])

        fill = trace.get("fill")
        fillcolor = trace.get("fillcolor")
        fill_color_opt = None
        fill_opacity = None

        libraries = set(self.libraries)
        if fill in ("tonexty", "tonextx"):
            libraries.add("fillbetween")

        if fill:
            target_col = fillcolor or color_str or "red"
            fcol_opt, fopacity = format_color(target_col)
            if fcol_opt:
                fill_color_opt = fcol_opt.replace("color=", "fill=")
            fill_opacity = fopacity if fopacity is not None else (trace_opacity if trace_opacity is not None else 0.3)

        name = trace.get("name")
        showlegend = trace.get("showlegend", True)
        legend_entry = escape_tex(name) if (name and showlegend is not False) else None

        return {
            "plot_cmd": r"\addplot+",
            "options": options,
            "options_str": ", ".join(options),
            "data_type": data_type,
            "table_content": table_content,
            "inline_coords": inline_coords,
            "tsv_filename": tsv_filename,
            "tsv_content": tsv_content,
            "legend_entry": legend_entry,
            "packages": self.packages,
            "libraries": libraries,
            "x_col": "x",
            "y_col": "y",
            "fill": fill,
            "fill_color_opt": fill_color_opt,
            "fill_opacity": fill_opacity,
        }
