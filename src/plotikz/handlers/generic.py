"""Fallback handler for generic or unhandled trace types."""

from typing import Dict, Any, Optional

from .base import TraceHandler
from ..utils import escape_tex, clean_val, format_coord_val


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
