"""Handler for Scatter, Scattergl, Scatter3d traces."""

from typing import Dict, Any, Optional, List
from .base import TraceHandler
from ..utils import format_color


class ScatterHandler(TraceHandler):
    """Handler for Scatter, Scattergl, Scatter3d traces."""

    def can_handle(self, trace_type: str) -> bool:
        return trace_type in ("scatter", "scattergl", "scatter3d", "")

    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
        base_dir: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        mode = trace.get("mode", "lines") or "lines"
        line_cfg = trace.get("line") or {}
        color_str = line_cfg.get("color") or (trace.get("marker") or {}).get("color")

        options = []
        options.extend(self._extract_line_options(trace, line_cfg, color_str))
        options.extend(self._extract_marker_options(trace, mode, color_str))

        coords = self._extract_xy_coords(trace)
        formatted_data = self._format_data_output(
            coords, trace_index, tsv_threshold, tsv_prefix, default_data_type="table_macro"
        )

        fill_info = self._extract_fill_options(trace, color_str)
        libraries = set(self.libraries)
        if fill_info["fill"] in ("tonexty", "tonextx"):
            libraries.add("fillbetween")

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
            "libraries": libraries,
            "x_col": "x",
            "y_col": "y",
            "fill": fill_info["fill"],
            "fill_color_opt": fill_info["fill_color_opt"],
            "fill_opacity": fill_info["fill_opacity"],
        }

    # -------------------------------------------------------------------------
    # Private Helper Methods (SRP)
    # -------------------------------------------------------------------------

    def _extract_line_options(
        self, trace: Dict[str, Any], line_cfg: Dict[str, Any], color_str: Optional[str]
    ) -> List[str]:
        """Extract PGFPlots options for line dash, width, step shape, and color/opacity."""
        options = []

        dash_opt = self._extract_line_dash(line_cfg)
        if dash_opt:
            options.append(dash_opt)

        line_width = line_cfg.get("width")
        if line_width is not None and isinstance(line_width, (int, float)):
            options.append(f"line width={line_width:g}pt")

        line_shape = line_cfg.get("shape") or trace.get("line_shape")
        if line_shape == "hv":
            options.append("const plot")
        elif line_shape == "vh":
            options.append("const plot mark right")

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

    @staticmethod
    def _extract_marker_options(trace: Dict[str, Any], mode: str, color_str: Optional[str]) -> List[str]:
        """Extract PGFPlots marker symbol, size, and marker color options."""
        options = []
        if "markers" not in mode:
            options.append("mark=none")
            return options

        if "lines" not in mode:
            options.append("only marks")

        marker = trace.get("marker") or {}
        symbol = marker.get("symbol", "circle")
        symbol_map = {
            "circle": "mark=*",
            "circle-open": "mark=o",
            "square": "mark=square*",
            "square-open": "mark=square",
            "diamond": "mark=diamond*",
            "diamond-open": "mark=diamond",
            "triangle-up": "mark=triangle*",
            "cross": "mark=x",
            "x": "mark=x",
            "star": "mark=asterisk",
        }
        if isinstance(symbol, str):
            base_sym = symbol.split("-")[0] if "-" in symbol else symbol
            options.append(symbol_map.get(symbol, symbol_map.get(base_sym, "mark=*")))
        else:
            options.append("mark=*")

        size = marker.get("size")
        if size is not None and isinstance(size, (int, float)):
            options.append(f"mark size={max(1.0, size / 2.5):g}pt")

        marker_color = (trace.get("marker") or {}).get("color") or color_str
        if isinstance(marker_color, str):
            mcol_opt, _ = format_color(marker_color)
            if mcol_opt:
                m_color = mcol_opt.replace("color=", "")
                options.append(f"mark options={{solid, fill={m_color}, draw={m_color}}}")
        else:
            options.append("mark options={solid}")

        return options

    @staticmethod
    def _extract_fill_options(trace: Dict[str, Any], color_str: Optional[str]) -> Dict[str, Any]:
        """Extract area fill settings (e.g. tonexty, tonextx)."""
        fill = trace.get("fill")
        fillcolor = trace.get("fillcolor")
        fill_color_opt = None
        fill_opacity = None

        if fill:
            target_col = fillcolor or color_str or "red"
            fcol_opt, fopacity = format_color(target_col)
            if fcol_opt:
                fill_color_opt = fcol_opt.replace("color=", "fill=")
            trace_opacity = trace.get("opacity")
            fill_opacity = fopacity if fopacity is not None else (trace_opacity if trace_opacity is not None else 0.3)

        return {
            "fill": fill,
            "fill_color_opt": fill_color_opt,
            "fill_opacity": fill_opacity,
        }
