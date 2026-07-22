"""Handler for Contour traces."""

import os
from typing import Dict, Any, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from .base import TraceHandler
from ..utils import escape_tex, clean_val, format_coord_val, format_color, format_colorscale, get_nice_ticks


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
    Exports the smooth 2D colormap background as a PNG image, inserts it via
    \\addplot graphics, and overlays smooth solid contour level lines matching colorbar ticks.
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
        raw_z = trace.get("z", [])
        if hasattr(raw_z, "tolist"):
            raw_z = raw_z.tolist()

        raw_x = trace.get("x")
        raw_y = trace.get("y")

        if hasattr(raw_x, "tolist"):
            raw_x = raw_x.tolist()
        if hasattr(raw_y, "tolist"):
            raw_y = raw_y.tolist()

        grid_z = []
        if raw_z:
            for row in raw_z:
                if hasattr(row, "tolist"):
                    row = row.tolist()
                grid_z.append([clean_val(v) for v in row])

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

        line_strs = []

        if num_rows > 0 and num_cols > 0:
            z_arr = np.array([[v if v is not None else 0 for v in row] for row in grid_z], dtype=float)
            x_arr = np.array(raw_x) if raw_x and len(raw_x) == num_cols else np.arange(1, num_cols + 1)
            y_arr = np.array(raw_y) if raw_y and len(raw_y) == num_rows else np.arange(1, num_rows + 1)
            X, Y = np.meshgrid(x_arr, y_arr)

            cs_val = trace.get("colorscale")
            if isinstance(cs_val, str) and cs_val.lower() != "plotly":
                try:
                    cmap = plt.get_cmap(cs_val.lower())
                except Exception:
                    cmap = mcolors.LinearSegmentedColormap.from_list("plotly", [c for _, c in PLOTLY_DEFAULT_STOPS])
            elif isinstance(cs_val, (list, tuple)):
                try:
                    colors = [c for _, c in cs_val]
                    cmap = mcolors.LinearSegmentedColormap.from_list("custom", colors)
                except Exception:
                    cmap = mcolors.LinearSegmentedColormap.from_list("plotly", [c for _, c in PLOTLY_DEFAULT_STOPS])
            else:
                cmap = mcolors.LinearSegmentedColormap.from_list("plotly", [c for _, c in PLOTLY_DEFAULT_STOPS])

            z_min = float(np.min(z_arr))
            z_max = float(np.max(z_arr))

            # 1. Render smooth background PNG
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.axis("off")
            fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
            ax.contourf(X, Y, z_arr, levels=50, cmap=cmap)

            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            fig.savefig(png_filepath, bbox_inches="tight", pad_inches=0, dpi=300)
            plt.close(fig)

            # 2. Extract solid contour level lines matching round ticks
            ticks = get_nice_ticks(z_min, z_max, max_ticks=5)
            fig_c, ax_c = plt.subplots()
            try:
                cs = ax_c.contour(X, Y, z_arr, levels=ticks)
            except Exception:
                cs = None

            if cs and hasattr(cs, "allsegs"):
                for level_segs in cs.allsegs:
                    for seg in level_segs:
                        if len(seg) > 0:
                            pts_str = " ".join([f"({x:.3f}, {y:.3f})" for x, y in seg])
                            line_strs.append(f"\\addplot+[mark=none, color=black, solid, line width=0.8pt] coordinates {{ {pts_str} }};")
            plt.close(fig_c)

        overlay_code = "\n".join(line_strs) if line_strs else ""
        plot_cmd = f"\\addplot graphics [xmin={x_min}, xmax={x_max}, ymin={y_min}, ymax={y_max}] {{{png_filename}}};"
        if overlay_code:
            plot_cmd = f"{plot_cmd}\n{overlay_code}"

        name = trace.get("name")
        showlegend = trace.get("showlegend", False)
        legend_entry = escape_tex(name) if (name and showlegend) else None

        return {
            "plot_cmd": "",
            "plot_code": plot_cmd,
            "options": [],
            "options_str": "",
            "data_type": "plot_code",
            "inline_coords": "",
            "tsv_filename": "",
            "tsv_content": "",
            "legend_entry": legend_entry,
            "packages": self.packages,
            "libraries": self.libraries,
            "x_col": "x",
            "y_col": "y",
        }
