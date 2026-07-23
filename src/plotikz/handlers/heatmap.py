"""Handler for Heatmap traces."""

from typing import Dict, Any, Optional, List, Tuple
from .base import TraceHandler
from ..utils import clean_val, format_coord_val


class HeatmapHandler(TraceHandler):
    """Handler for Heatmap traces."""

    def __init__(self):
        super().__init__()
        self.libraries.add("colormaps")

    def can_handle(self, trace_type: str) -> bool:
        return trace_type == "heatmap"

    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
        base_dir: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        raw_z = self._to_list(trace.get("z", []))
        num_cols = self._compute_num_cols(raw_z)

        options = ["matrix plot*", f"mesh/cols={num_cols}", "point meta=explicit", "mark=none"]
        colorscale = trace.get("colorscale")
        if isinstance(colorscale, str):
            options.append(f"colormap/{colorscale.lower()}")

        raw_x = self._to_list(trace.get("x"))
        raw_y = self._to_list(trace.get("y"))

        coords = self._extract_heatmap_coords(raw_x, raw_y, raw_z)
        formatted_data = self._format_data_output(
            coords, trace_index, tsv_threshold, tsv_prefix, default_data_type="table_macro", cols=("x", "y", "z")
        )
        legend_entry = self._extract_legend_entry(trace, default_showlegend=False)

        return {
            "plot_cmd": r"\addplot+",
            "options": options,
            "options_str": ", ".join(options),
            "data_type": formatted_data["data_type"],
            "table_content": formatted_data["table_content"],
            "table_opts": "meta=z",
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

    def _compute_num_cols(self, raw_z: List[Any]) -> int:
        """Determine grid column count from matrix z data."""
        if raw_z and isinstance(raw_z, list):
            first_row = self._to_list(raw_z[0])
            if isinstance(first_row, list):
                return len(first_row)
        return 1

    def _extract_heatmap_coords(
        self, raw_x: List[Any], raw_y: List[Any], raw_z: List[Any]
    ) -> List[Tuple[str, str, str]]:
        """Extract cleaned and formatted (x, y, z) 3D coordinate tuples."""
        coords = []
        if raw_z:
            for r_idx, row in enumerate(raw_z):
                row_list = self._to_list(row)
                y_val = raw_y[r_idx] if raw_y and r_idx < len(raw_y) else r_idx + 1
                for c_idx, z_val in enumerate(row_list):
                    x_val = raw_x[c_idx] if raw_x and c_idx < len(raw_x) else c_idx + 1
                    cz = clean_val(z_val)
                    if cz is not None:
                        coords.append((format_coord_val(x_val), format_coord_val(y_val), format_coord_val(cz)))
        return coords
