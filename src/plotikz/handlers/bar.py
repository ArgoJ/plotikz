"""Handler for Bar traces."""

from typing import Dict, Any, Optional

from .base import TraceHandler
from ..utils import format_color, escape_tex, clean_val, format_coord_val


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
        base_dir: Optional[str] = None,
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
                draw_opt = col_opt.replace("color=", "draw=")
                options.append(fill_opt)
                options.append(draw_opt)
            if opacity is not None and opacity < 1.0:
                options.append(f"fill opacity={opacity}")
        else:
            options.append("draw=none")

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
            table_content = ""
            inline_coords = ""
        else:
            data_type = "table_macro"
            tsv_filename = ""
            tsv_content = ""
            lines = ["x y"] + [f"{x} {y}" for x, y in coords]
            table_content = "\n".join(lines)
            inline_coords = " ".join([f"({x}, {y})" for x, y in coords])

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
            "libraries": self.libraries,
            "x_col": "x",
            "y_col": "y",
        }
