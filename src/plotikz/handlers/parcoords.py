"""Handler for Parcoords (Parallel Coordinates) traces."""

from typing import Dict, Any, Optional, List, Tuple
from .base import TraceHandler
from ..utils import clean_val, format_coord_val, format_color


class ParcoordsHandler(TraceHandler):
    """Handler for Plotly Parcoords (Parallel Coordinates) traces."""

    def can_handle(self, trace_type: str) -> bool:
        return trace_type == "parcoords"

    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        options = ["mark=none", "unbounded coords=jump"]
        options.extend(self._extract_parcoords_line_options(trace))

        dimensions = self._parse_dimensions(trace)
        parsed_dims, max_rows = self._parse_dimension_values(dimensions)

        observations, total_points = self._build_observations(parsed_dims, max_rows)
        coords = self._flatten_observations(observations)

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

    def _extract_parcoords_line_options(self, trace: Dict[str, Any]) -> List[str]:
        """Extract line dash, width, and color/opacity options."""
        options = []
        line = trace.get("line") or {}
        if isinstance(line, dict):
            dash_opt = self._extract_line_dash(line)
            if dash_opt:
                options.append(dash_opt)

            line_width = line.get("width")
            if line_width is not None and isinstance(line_width, (int, float)):
                options.append(f"line width={line_width}pt")

            color_str = line.get("color")
            if isinstance(color_str, str):
                col_opt, opacity = format_color(color_str)
                if col_opt:
                    options.append(col_opt)
                if opacity is not None and opacity < 1.0:
                    options.append(f"opacity={opacity}")

        trace_opacity = trace.get("opacity")
        if trace_opacity is not None and isinstance(trace_opacity, (int, float)) and trace_opacity < 1.0:
            options.append(f"opacity={trace_opacity}")

        return options

    def _parse_dimensions(self, trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize raw dimensions into list of dicts."""
        raw_dims = trace.get("dimensions", [])
        dimensions = []
        for d in raw_dims:
            if hasattr(d, "to_plotly_json"):
                dimensions.append(d.to_plotly_json())
            elif hasattr(d, "to_dict"):
                dimensions.append(d.to_dict())
            elif isinstance(d, dict):
                dimensions.append(d)
            else:
                try:
                    dimensions.append(dict(d))
                except Exception:
                    pass
        return dimensions

    def _parse_dimension_values(self, dimensions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Extract cleaned values and min/max ranges per dimension."""
        max_rows = 0
        parsed_dims = []
        for dim in dimensions:
            vals = self._to_list(dim.get("values", []))
            clean_vals = [clean_val(v) for v in vals]
            if len(clean_vals) > max_rows:
                max_rows = len(clean_vals)

            d_range = dim.get("range")
            min_val, max_val = None, None
            if d_range and isinstance(d_range, (list, tuple)) and len(d_range) == 2:
                try:
                    min_val = float(d_range[0])
                    max_val = float(d_range[1])
                except (ValueError, TypeError):
                    pass

            if min_val is None or max_val is None or min_val == max_val:
                numeric_vals = [v for v in clean_vals if isinstance(v, (int, float))]
                if numeric_vals:
                    min_val = min(numeric_vals)
                    max_val = max(numeric_vals)
                else:
                    min_val, max_val = 0.0, 1.0

            parsed_dims.append({
                "values": clean_vals,
                "min": min_val,
                "max": max_val,
            })
        return parsed_dims, max_rows

    @staticmethod
    def _build_observations(
        parsed_dims: List[Dict[str, Any]], max_rows: int
    ) -> Tuple[List[List[Tuple[int, Optional[float]]]], int]:
        """Build normalized observation coordinates across parallel axes."""
        observations = []
        total_points = 0
        num_dims = len(parsed_dims)

        for row_idx in range(max_rows):
            obs_coords = []
            for dim_idx in range(num_dims):
                dim_info = parsed_dims[dim_idx]
                vals = dim_info["values"]
                v = vals[row_idx] if row_idx < len(vals) else None
                x_coord = dim_idx + 1

                if v is not None and isinstance(v, (int, float)):
                    min_v = dim_info["min"]
                    max_v = dim_info["max"]
                    y_norm = (v - min_v) / (max_v - min_v) if max_v > min_v else 0.5
                    obs_coords.append((x_coord, y_norm))
                else:
                    obs_coords.append((x_coord, None))

            if any(y is not None for _, y in obs_coords):
                observations.append(obs_coords)
                total_points += len(obs_coords)

        return observations, total_points

    @staticmethod
    def _flatten_observations(observations: List[List[Tuple[int, Optional[float]]]]) -> List[Tuple[str, str]]:
        """Flatten observation paths into coordinate pairs separated by nan jumpers."""
        coords = []
        for obs_idx, obs in enumerate(observations):
            for x, y in obs:
                y_str = format_coord_val(y) if y is not None else "nan"
                coords.append((str(x), y_str))
            if obs_idx < len(observations) - 1:
                coords.append(("nan", "nan"))
        return coords
