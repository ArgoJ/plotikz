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
    ) -> Dict[str, Any]:
        prefix = tsv_prefix or "data"
        raw_z = self._to_list(trace.get("z", []))
        raw_x = self._to_list(trace.get("x"))
        raw_y = self._to_list(trace.get("y"))

        grid_z = self._process_grid_z(raw_z, raw_x, raw_y)
        num_rows = len(grid_z)
        num_cols = len(grid_z[0]) if num_rows > 0 else 0

        x_min = raw_x[0] if raw_x and len(raw_x) > 0 else 1
        x_max = raw_x[-1] if raw_x and len(raw_x) > 0 else (num_cols if num_cols > 0 else 1)
        y_min = raw_y[0] if raw_y and len(raw_y) > 0 else 1
        y_max = raw_y[-1] if raw_y and len(raw_y) > 0 else (num_rows if num_rows > 0 else 1)

        png_filename = f"{prefix}_contour_{trace_index}.png"
        png_filepath = os.path.join(base_dir, png_filename) if base_dir else png_filename
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)

        contours_cfg = trace.get("contours", {})
        is_constraint = contours_cfg.get("type") == "constraint"
        raw_name = trace.get("name") or ("ROA" if is_constraint else "Contour")

        extra_tables = []
        bg_cmd = None

        if num_rows > 0 and num_cols > 0:
            z_arr = np.array([[v if v is not None else 0 for v in row] for row in grid_z], dtype=float)
            x_arr = np.array(raw_x) if raw_x and len(raw_x) == num_cols else np.arange(1, num_cols + 1)
            y_arr = np.array(raw_y) if raw_y and len(raw_y) == num_rows else np.arange(1, num_rows + 1)
            X, Y = np.meshgrid(x_arr, y_arr)

            if is_constraint:
                extra_tables = self._generate_constraint_contour(X, Y, z_arr, trace, raw_name)
            else:
                bg_cmd, extra_tables = self._generate_full_contour(
                    X, Y, z_arr, trace, raw_name, png_filepath, png_filename, (x_min, x_max, y_min, y_max)
                )

        legend_entry = self._extract_legend_entry(trace, default_showlegend=False)

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

    def _generate_constraint_contour(
        self, X: np.ndarray, Y: np.ndarray, z_arr: np.ndarray, trace: Dict[str, Any], raw_name: str
    ) -> List[Dict[str, Any]]:
        """Generate table entries for single level constraint contour lines (e.g. ROA boundary)."""
        extra_tables = []
        contours_cfg = trace.get("contours", {})
        constraint_value = contours_cfg.get("value")
        line_cfg = trace.get("line", {})
        line_color = line_cfg.get("color", "black")
        line_width = line_cfg.get("width", 1.5)

        tikz_dash = self._extract_line_dash(line_cfg) or "solid"
        levels = [constraint_value] if constraint_value is not None else []

        if levels:
            fig_c, ax_c = plt.subplots()
            try:
                cs = ax_c.contour(X, Y, z_arr, levels=levels)
                if hasattr(cs, "allsegs"):
                    col_str, _ = format_color(line_color)
                    col_str = col_str or "color=red"
                    seg_idx = 0
                    for level_segs in cs.allsegs:
                        for seg in level_segs:
                            if len(seg) > 0:
                                table_lines = ["x y"] + [f"{x:.4f} {y:.4f}" for x, y in seg]
                                hint = f"{raw_name}Constraint{seg_idx}" if seg_idx > 0 else f"{raw_name}Constraint"
                                extra_tables.append({
                                    "name_hint": hint,
                                    "table_content": "\n".join(table_lines),
                                    "plot_cmd": f"\\addplot+[mark=none, {col_str}, {tikz_dash}, line width={line_width}pt]"
                                })
                                seg_idx += 1
            except Exception:
                pass
            finally:
                plt.close(fig_c)

        return extra_tables

    def _generate_full_contour(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        z_arr: np.ndarray,
        trace: Dict[str, Any],
        raw_name: str,
        png_filepath: str,
        png_filename: str,
        bounds: Tuple[float, float, float, float],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate smooth background PNG and level line macro tables for a full contour plot."""
        x_min, x_max, y_min, y_max = bounds
        extra_tables = []

        cmap = self._get_matplotlib_colormap(trace.get("colorscale"))
        z_min = float(np.min(z_arr))
        z_max = float(np.max(z_arr))

        # Render background PNG
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.axis("off")
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        ax.contourf(X, Y, z_arr, levels=50, cmap=cmap)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        fig.savefig(png_filepath, bbox_inches="tight", pad_inches=0, dpi=300)
        plt.close(fig)

        bg_cmd = f"\\addplot graphics [xmin={x_min}, xmax={x_max}, ymin={y_min}, ymax={y_max}] {{{png_filename}}};"

        # Extract contour level lines matching ticks
        ticks = get_nice_ticks(z_min, z_max, max_ticks=5)
        fig_c, ax_c = plt.subplots()
        try:
            cs = ax_c.contour(X, Y, z_arr, levels=ticks)
        except Exception:
            cs = None

        if cs and hasattr(cs, "allsegs"):
            seg_idx = 0
            for level_segs in cs.allsegs:
                for seg in level_segs:
                    if len(seg) > 0:
                        table_lines = ["x y"] + [f"{x:.4f} {y:.4f}" for x, y in seg]
                        hint = f"{raw_name}Line{seg_idx}"
                        extra_tables.append({
                            "name_hint": hint,
                            "table_content": "\n".join(table_lines),
                            "plot_cmd": "\\addplot+[mark=none, color=black, solid, line width=0.8pt]"
                        })
                        seg_idx += 1
        plt.close(fig_c)

        return bg_cmd, extra_tables

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
