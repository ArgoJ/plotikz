"""Handler for Parcoords (Parallel Coordinates) traces."""

from typing import Dict, Any, Optional
from .base import TraceHandler
from ..utils import escape_tex, clean_val, format_coord_val, format_color


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

        line = trace.get("line") or {}
        if isinstance(line, dict):
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

        raw_dimensions = trace.get("dimensions", [])
        dimensions = []
        for d in raw_dimensions:
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

        max_rows = 0
        parsed_dims = []
        for dim in dimensions:
            vals = dim.get("values", [])
            if hasattr(vals, "tolist"):
                vals = vals.tolist()
            elif hasattr(vals, "values"):
                vals = vals.values.tolist()

            clean_vals = [clean_val(v) for v in vals]
            if len(clean_vals) > max_rows:
                max_rows = len(clean_vals)

            d_range = dim.get("range")
            min_val = None
            max_val = None
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
                    if max_v > min_v:
                        y_norm = (v - min_v) / (max_v - min_v)
                    else:
                        y_norm = 0.5
                    obs_coords.append((x_coord, y_norm))
                else:
                    obs_coords.append((x_coord, None))

            if any(y is not None for _, y in obs_coords):
                observations.append(obs_coords)
                total_points += len(obs_coords)

        prefix = tsv_prefix or "data"

        if total_points > tsv_threshold:
            data_type = "tsv"
            tsv_filename = f"{prefix}_trace_{trace_index}.tsv"
            tsv_lines = ["x\ty"]
            for obs in observations:
                for x, y in obs:
                    y_str = format_coord_val(y) if y is not None else "nan"
                    tsv_lines.append(f"{x}\t{y_str}")
                tsv_lines.append("")
            tsv_content = "\n".join(tsv_lines)
            table_content = ""
            inline_coords = ""
        else:
            data_type = "table_macro"
            tsv_filename = ""
            tsv_content = ""
            lines = ["x y"]
            for obs in observations:
                for x, y in obs:
                    y_str = format_coord_val(y) if y is not None else "nan"
                    lines.append(f"{x} {y_str}")
                lines.append("nan nan")
            if lines and lines[-1] == "nan nan":
                lines.pop()
            table_content = "\n".join(lines)
            obs_strings = []
            for obs in observations:
                coord_strs = []
                for x, y in obs:
                    y_str = format_coord_val(y) if y is not None else "nan"
                    coord_strs.append(f"({x}, {y_str})")
                obs_strings.append(" ".join(coord_strs))
            inline_coords = "\n\n".join(obs_strings)

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
