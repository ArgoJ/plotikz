"""Fallback handler for generic or unhandled trace types."""

from typing import Dict, Any, Optional
from .base import TraceHandler


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
        base_dir: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        options = ["mark=none"]
        coords = self._extract_xy_coords(trace)
        formatted_data = self._format_data_output(
            coords, trace_index, tsv_threshold, tsv_prefix, default_data_type="inline"
        )
        legend_entry = self._extract_legend_entry(trace, default_showlegend=True)

        return {
            "plot_cmd": r"\addplot+",
            "options": options,
            "options_str": ", ".join(options),
            "data_type": formatted_data["data_type"],
            "inline_coords": formatted_data["inline_coords"],
            "tsv_filename": formatted_data["tsv_filename"],
            "tsv_content": formatted_data["tsv_content"],
            "legend_entry": legend_entry,
            "packages": self.packages,
            "libraries": self.libraries,
            "x_col": "x",
            "y_col": "y",
        }
