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
            # Flat 1D z array (e.g. from bdata decoding) → reshape to 2D
            if raw_z and not isinstance(raw_z[0], (list, tuple)):
                n_x = len(raw_x) if raw_x else int(len(raw_z) ** 0.5)
                n_y = len(raw_y) if raw_y else int(len(raw_z) ** 0.5)
                if n_x * n_y == len(raw_z):
                    raw_z = [raw_z[i * n_x:(i + 1) * n_x] for i in range(n_y)]
                else:
                    n = int(len(raw_z) ** 0.5)
                    raw_z = [raw_z[i * n:(i + 1) * n] for i in range(n)]

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

        # Detect constraint contour (e.g. ROA boundary) vs full contour plot
        contours_cfg = trace.get("contours", {})
        is_constraint = contours_cfg.get("type") == "constraint"
        constraint_value = contours_cfg.get("value")
        line_cfg = trace.get("line", {})
        line_color = line_cfg.get("color", "black")
        line_dash = line_cfg.get("dash", "solid")
        line_width = line_cfg.get("width", 1.5)

        # Map Plotly dash styles to TikZ
        dash_map = {"dash": "dashed", "dot": "dotted", "dashdot": "dash dot"}
        tikz_dash = dash_map.get(line_dash, "solid")

        if num_rows > 0 and num_cols > 0:
            z_arr = np.array([[v if v is not None else 0 for v in row] for row in grid_z], dtype=float)
            x_arr = np.array(raw_x) if raw_x and len(raw_x) == num_cols else np.arange(1, num_cols + 1)
            y_arr = np.array(raw_y) if raw_y and len(raw_y) == num_rows else np.arange(1, num_rows + 1)
            X, Y = np.meshgrid(x_arr, y_arr)

            if is_constraint:
                # ----- Constraint contour: draw only a contour line, no background -----
                levels = [constraint_value] if constraint_value is not None else []
                if levels:
                    fig_c, ax_c = plt.subplots()
                    try:
                        cs = ax_c.contour(X, Y, z_arr, levels=levels)
                        if hasattr(cs, "allsegs"):
                            col_str, _ = format_color(line_color)
                            col_str = col_str or "color=red"
                            for level_segs in cs.allsegs:
                                for seg in level_segs:
                                    if len(seg) > 0:
                                        pts_str = " ".join([f"({x:.3f}, {y:.3f})" for x, y in seg])
                                        line_strs.append(
                                            f"\\addplot+[mark=none, {col_str}, {tikz_dash}, "
                                            f"line width={line_width}pt] coordinates {{ {pts_str} }};"
                                        )
                    except Exception:
                        pass
                    finally:
                        plt.close(fig_c)

                plot_cmd = "\n".join(line_strs)

            else:
                # ----- Full contour: render background PNG + overlay contour lines -----
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

                # Render smooth background PNG
                fig, ax = plt.subplots(figsize=(6, 6))
                ax.axis("off")
                fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
                ax.contourf(X, Y, z_arr, levels=50, cmap=cmap)
                ax.set_xlim(x_min, x_max)
                ax.set_ylim(y_min, y_max)
                fig.savefig(png_filepath, bbox_inches="tight", pad_inches=0, dpi=300)
                plt.close(fig)

                # Extract solid contour level lines matching round ticks
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

        else:
            plot_cmd = ""

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

