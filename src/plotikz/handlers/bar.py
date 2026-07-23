"""Handler for Bar traces."""

from typing import Dict, Any, Optional, List
from .base import TraceHandler
from ..utils import format_color


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
        **kwargs,
    ) -> Dict[str, Any]:
        orientation = trace.get("orientation", "v")
        options = ["xbar"] if orientation == "h" else ["ybar"]
        options.extend(self._extract_bar_color_options(trace))

        coords = self._extract_xy_coords(trace)
        formatted_data = self._format_data_output(
            coords, trace_index, tsv_threshold, tsv_prefix, default_data_type="table_macro"
        )
        legend_entry = self._extract_legend_entry(trace, default_showlegend=True)

        return {
            "plot_cmd": r"\addplot+",
            "options": options,
            "options_str": ", ".join(options),
            "data_type": formatted_data["data_type"],
            "table_content": formatted_data["table_content"],
            "inline_coords": formatted_data["inline_coords"],
            "tsv_filename": formatted_data["tsv_filename"],
            "tsv_content": formatted_data["tsv_content"],
            "legend_entry": legend_entry,
            "packages": self.packages,
            "libraries": self.libraries,
            "x_col": "x",
            "y_col": "y",
        }

    # -------------------------------------------------------------------------
    # Private Helper Methods (SRP)
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_bar_color_options(trace: Dict[str, Any]) -> List[str]:
        """Extract bar fill/draw colors and opacity options from trace marker."""
        options = []
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
        return options
