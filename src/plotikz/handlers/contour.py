"""Handler for Contour traces."""

from typing import Dict, Any, Optional

from .base import TraceHandler
from ..utils import escape_tex, clean_val, format_coord_val, format_color


class ContourHandler(TraceHandler):
    """Handler for Contour traces."""

    def __init__(self):
        super().__init__()
        self.libraries.add("colormaps")
        self.libraries.add("contour")

    def can_handle(self, trace_type: str) -> bool:
        return trace_type == "contour"

    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        options = ["contour filled", "point meta=explicit"]

        contours = trace.get("contours", {})
        showlines = contours.get("showlines", True) if isinstance(contours, dict) else True
        showlabels = contours.get("showlabels", False) if isinstance(contours, dict) else False

        if showlines:
            line_dict = trace.get("line") or (contours.get("line") if isinstance(contours, dict) else None)
            line_color_str = line_dict.get("color") if isinstance(line_dict, dict) else None

            if line_color_str:
                color_opt, _ = format_color(line_color_str)
                if color_opt and color_opt.startswith("color="):
                    raw_color = color_opt[len("color="):]
                    options.append(f"contour/draw color={raw_color}")
                else:
                    options.append("contour/draw color=black")
            else:
                options.append("contour/draw color=black")
        else:
            options.append("contour/draw color=none")

        if showlabels:
            options.append("contour/labels=true")
        else:
            options.append("contour/labels=false")

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
