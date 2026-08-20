"""Handler for Contour traces."""

import os
import numpy as np

from typing import Dict, Any, Optional, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from .base import TraceHandler
from ..utils import clean_val, format_color, get_nice_ticks


PLOTLY_DEFAULT_STOPS = [
    (0.0, "#0d0887"),
    (0.1111111111111111, "#46039f"),
    (0.2222222222222222, "#7201a8"),
    (0.3333333333333333, "#9c179e"),
    (0.4444444444444444, "#bd3786"),
    (0.5555555555555556, "#d8576b"),
    (0.6666666666666666, "#ed7953"),
    (0.7777777777777778, "#fb9f3a"),
    (0.8888888888888888, "#fdca26"),
    (1.0, "#f0f921"),
]


class ContourHandler(TraceHandler):
    """
    Handler for Contour traces.
    Exports smooth 2D colormap background as a PNG image, inserts it via
    \\addplot graphics, and exports contour level lines as pgfplotstableread macro tables.
    """

    def __init__(self):
        super().__init__()
        self.libraries.add("colormaps")

    def can_handle(self, trace_type: str) -> bool:
        return trace_type == "contour"

    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
        base_dir: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        prefix = tsv_prefix or "data"
        colorbar_ticks = kwargs.get("colorbar_ticks", 5)
        color_registry = kwargs.get("color_registry")
        raw_z = self._to_list(trace.get("z", []))
        raw_x = self._to_list(trace.get("x"))
        raw_y = self._to_list(trace.get("y"))

        grid_z = self._process_grid_z(raw_z, raw_x, raw_y)
        num_rows = len(grid_z)
        num_cols = len(grid_z[0]) if num_rows > 0 else 0

        if num_rows == 0 or num_cols == 0:
            return {
                "plot_cmd": "",
                "plot_code": "",
                "bg_cmd": None,
                "options": [],
                "options_str": "",
                "data_type": "plot_code",
                "inline_coords": "",
                "tsv_filename": "",
                "tsv_content": "",
                "legend_entry": None,
                "packages": self.packages,
                "libraries": self.libraries,
                "extra_tables": [],
                "x_col": "x",
                "y_col": "y",
            }

        x_min = raw_x[0] if raw_x and len(raw_x) > 0 else 1
        x_max = raw_x[-1] if raw_x and len(raw_x) > 0 else (num_cols if num_cols > 0 else 1)
        y_min = raw_y[0] if raw_y and len(raw_y) > 0 else 1
        y_max = raw_y[-1] if raw_y and len(raw_y) > 0 else (num_rows if num_rows > 0 else 1)

        contours_cfg = trace.get("contours", {})
        coloring = contours_cfg.get("coloring", "fill")
        is_constraint = contours_cfg.get("type") == "constraint"
        raw_name = trace.get("name") or ("ROA" if is_constraint else "Contour")

        has_bg = (coloring not in ("none", "lines")) and (not is_constraint)
        legend_entry = self._extract_legend_entry(trace, default_showlegend=False)

        z_arr = np.array([[v if v is not None else 0 for v in row] for row in grid_z], dtype=float)
        x_arr = np.array(raw_x) if raw_x and len(raw_x) == num_cols else np.arange(1, num_cols + 1)
        y_arr = np.array(raw_y) if raw_y and len(raw_y) == num_rows else np.arange(1, num_rows + 1)
        X, Y = np.meshgrid(x_arr, y_arr)

        bg_cmd = None
        if has_bg:
            png_filename = f"{prefix}_contour_{trace_index}.png"
            png_filepath = os.path.join(base_dir, png_filename) if base_dir else png_filename
            if base_dir:
                os.makedirs(base_dir, exist_ok=True)
            bg_cmd = self._generate_background_image(
                X, Y, z_arr, trace, png_filepath, png_filename, (x_min, x_max, y_min, y_max)
            )

        levels = self._extract_contour_levels(contours_cfg, z_arr, colorbar_ticks=colorbar_ticks)
        extra_tables = self._generate_contour_lines(
            X, Y, z_arr, trace, raw_name, levels, legend_entry=legend_entry, color_registry=color_registry
        )

        return {
            "plot_cmd": "",
            "plot_code": "",
            "bg_cmd": bg_cmd,
            "options": [],
            "options_str": "",
            "data_type": "plot_code",
            "inline_coords": "",
            "tsv_filename": "",
            "tsv_content": "",
            "legend_entry": legend_entry,
            "packages": self.packages,
            "libraries": self.libraries,
            "extra_tables": extra_tables,
            "x_col": "x",
            "y_col": "y",
        }

    # -------------------------------------------------------------------------
    # Private Helper Methods (SRP)
    # -------------------------------------------------------------------------

    def _process_grid_z(self, raw_z: List[Any], raw_x: List[Any], raw_y: List[Any]) -> List[List[Any]]:
        """Normalize raw z data into clean 2D grid matrix."""
        grid_z = []
        if raw_z:
            # Reshape flat 1D z array (e.g. from bdata decoding) to 2D
            if not isinstance(raw_z[0], (list, tuple)):
                n_x = len(raw_x) if raw_x else int(len(raw_z) ** 0.5)
                n_y = len(raw_y) if raw_y else int(len(raw_z) ** 0.5)
                if n_x * n_y == len(raw_z):
                    raw_z = [raw_z[i * n_x:(i + 1) * n_x] for i in range(n_y)]
                else:
                    n = int(len(raw_z) ** 0.5)
                    raw_z = [raw_z[i * n:(i + 1) * n] for i in range(n)]

            for row in raw_z:
                row_list = self._to_list(row)
                grid_z.append([clean_val(v) for v in row_list])
        return grid_z

    def _extract_contour_levels(
        self, contours_cfg: Dict[str, Any], z_arr: np.ndarray, colorbar_ticks: int = 5
    ) -> List[float]:
        """Extract explicit or calculated contour levels from contour config."""
        is_constraint = contours_cfg.get("type") == "constraint"
        if is_constraint:
            val = contours_cfg.get("value")
            if val is not None:
                if isinstance(val, (int, float)):
                    return [float(val)]
                elif isinstance(val, (list, tuple)):
                    return [float(v) for v in val]
            return []

        if contours_cfg.get("start") is not None:
            start = float(contours_cfg["start"])
            end = float(contours_cfg.get("end", start))
            size = float(contours_cfg.get("size", 1.0)) if contours_cfg.get("size") else 1.0
            if abs(start - end) < 1e-9 or start == end or size <= 0:
                return [start]
            num_steps = int(np.floor((end - start) / size + 1e-6)) + 1
            return [start + i * size for i in range(num_steps)]

        if contours_cfg.get("value") is not None:
            return [float(contours_cfg["value"])]

        if contours_cfg.get("showlines") is False:
            return []

        z_min = float(np.min(z_arr))
        z_max = float(np.max(z_arr))
        return get_nice_ticks(z_min, z_max, max_ticks=max(1, colorbar_ticks))

    def _generate_background_image(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        z_arr: np.ndarray,
        trace: Dict[str, Any],
        png_filepath: str,
        png_filename: str,
        bounds: Tuple[float, float, float, float],
    ) -> str:
        """Render smooth 2D colormap background as a PNG image."""
        x_min, x_max, y_min, y_max = bounds
        cmap = self._get_matplotlib_colormap(trace.get("colorscale"))

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.axis("off")
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        ax.contourf(X, Y, z_arr, levels=50, cmap=cmap)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        fig.savefig(png_filepath, bbox_inches="tight", pad_inches=0, dpi=300)
        plt.close(fig)

        return f"\\addplot [forget plot] graphics [xmin={x_min}, xmax={x_max}, ymin={y_min}, ymax={y_max}] {{{png_filename}}};"

    def _generate_contour_lines(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        z_arr: np.ndarray,
        trace: Dict[str, Any],
        raw_name: str,
        levels: List[float],
        legend_entry: Optional[str] = None,
        color_registry: Any = None,
    ) -> List[Dict[str, Any]]:
        """Generate table entries for contour lines matching levels."""
        if not levels:
            return []

        line_cfg = trace.get("line", {})
        line_color = line_cfg.get("color")
        if line_color:
            col_str, _ = format_color(line_color, color_registry=color_registry)
            col_str = col_str or "color=black"
        else:
            col_str = "color=black"

        dash_str = self._extract_line_dash(line_cfg) or "solid"
        line_width = line_cfg.get("width")
        if line_width is not None and isinstance(line_width, (int, float)):
            width_str = f"line width={line_width:g}pt"
        else:
            width_str = "line width=0.8pt"

        trace_opacity = trace.get("opacity")
        opacity_str = (
            f", opacity={trace_opacity:g}"
            if (trace_opacity is not None and isinstance(trace_opacity, (int, float)) and trace_opacity < 1.0)
            else ""
        )

        base_opts = f"mark=none, {col_str}, {dash_str}, {width_str}{opacity_str}"

        # Extract contour segments with matplotlib
        fig_c, ax_c = plt.subplots()
        extracted_segments = []
        try:
            cs = ax_c.contour(X, Y, z_arr, levels=levels)
            if hasattr(cs, "allsegs"):
                for level_segs in cs.allsegs:
                    for seg in level_segs:
                        if len(seg) > 0:
                            extracted_segments.append(seg)
        except Exception:
            pass
        finally:
            plt.close(fig_c)

        extra_tables = []
        num_segs = len(extracted_segments)
        for seg_idx, seg in enumerate(extracted_segments):
            table_lines = ["x y"] + [f"{x:.4f} {y:.4f}" for x, y in seg]
            hint = f"{raw_name}Line{seg_idx}" if seg_idx > 0 else f"{raw_name}Line"

            # In PGFPlots, if trace has no legend, forget plot for all segments.
            # If trace has a legend, forget plot for all segments except the last one.
            if legend_entry is None or seg_idx < num_segs - 1:
                plot_cmd = f"\\addplot+[{base_opts}, forget plot]"
            else:
                plot_cmd = f"\\addplot+[{base_opts}]"

            extra_tables.append({
                "name_hint": hint,
                "table_content": "\n".join(table_lines),
                "plot_cmd": plot_cmd,
            })

        return extra_tables

    @staticmethod
    def _get_matplotlib_colormap(cs_val: Any) -> mcolors.Colormap:
        """Convert Plotly colorscale definition to Matplotlib colormap object."""
        if isinstance(cs_val, str) and cs_val.lower() != "plotly":
            try:
                return plt.get_cmap(cs_val.lower())
            except Exception:
                return mcolors.LinearSegmentedColormap.from_list("plotly", [c for _, c in PLOTLY_DEFAULT_STOPS])
        elif isinstance(cs_val, (list, tuple)):
            try:
                colors = [c for _, c in cs_val]
                return mcolors.LinearSegmentedColormap.from_list("custom", colors)
            except Exception:
                return mcolors.LinearSegmentedColormap.from_list("plotly", [c for _, c in PLOTLY_DEFAULT_STOPS])
        return mcolors.LinearSegmentedColormap.from_list("plotly", [c for _, c in PLOTLY_DEFAULT_STOPS])
