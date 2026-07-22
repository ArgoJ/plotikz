"""Main converter module for Plotly to TikZ/PGFPlots translation."""

import os
from typing import Dict, Any, List, Optional, Tuple, Union
from jinja2 import Environment, PackageLoader, FileSystemLoader, ChoiceLoader

from .registry import TraceRegistry, default_registry
from .utils import escape_tex


class PlotlyToTikz:
    """Converter for Plotly figures to LaTeX/TikZ PGFPlots code."""

    def __init__(self, registry: Optional[TraceRegistry] = None):
        """Initialize converter with optional custom trace registry."""
        self.registry = registry or default_registry

        # Setup Jinja2 environment with LaTeX-safe delimiters
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        loaders = [FileSystemLoader(template_dir)]
        try:
            loaders.append(PackageLoader("plotikz", "templates"))
        except Exception:
            pass

        self.env = Environment(
            loader=ChoiceLoader(loaders),
            block_start_string="<%",
            block_end_string="%>",
            variable_start_string="<<",
            variable_end_string=">>",
            comment_start_string="<#",
            comment_end_string="#>",
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _parse_figure(self, fig: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Normalize input figure into list of trace dicts and layout dict."""
        traces = []
        layout = {}

        if isinstance(fig, dict):
            traces = fig.get("data", [])
            layout = fig.get("layout", {})
        elif hasattr(fig, "to_dict"):
            fig_dict = fig.to_dict()
            traces = fig_dict.get("data", [])
            layout = fig_dict.get("layout", {})
        elif isinstance(fig, list):
            traces = fig
            layout = {}
        elif hasattr(fig, "data") and hasattr(fig, "layout"):
            traces = fig.data
            layout = fig.layout
            if hasattr(layout, "to_dict"):
                layout = layout.to_dict()

        normalized_traces = []
        for t in traces:
            if hasattr(t, "to_plotly_json"):
                normalized_traces.append(t.to_plotly_json())
            elif hasattr(t, "to_dict"):
                normalized_traces.append(t.to_dict())
            elif isinstance(t, dict):
                normalized_traces.append(t)
            else:
                try:
                    normalized_traces.append(dict(t))
                except Exception:
                    pass

        return normalized_traces, layout

    def _build_axis_options(self, layout: Dict[str, Any]) -> List[str]:
        """Convert Plotly layout dictionary into PGFPlots axis options."""
        options = []

        # Title
        title = layout.get("title")
        if isinstance(title, dict):
            title_text = title.get("text", "")
        else:
            title_text = str(title) if title is not None else ""
        if title_text:
            options.append(f"title={{{escape_tex(title_text)}}}")

        # X-axis
        xaxis = layout.get("xaxis") or {}
        xtitle = xaxis.get("title")
        if isinstance(xtitle, dict):
            xtitle_text = xtitle.get("text", "")
        else:
            xtitle_text = str(xtitle) if xtitle is not None else ""
        if xtitle_text:
            options.append(f"xlabel={{{escape_tex(xtitle_text)}}}")

        if xaxis.get("type") == "log":
            options.append("xmode=log")

        xrange = xaxis.get("range")
        if xrange and isinstance(xrange, (list, tuple)) and len(xrange) == 2:
            options.append(f"xmin={xrange[0]}")
            options.append(f"xmax={xrange[1]}")

        if xaxis.get("showgrid") is True:
            options.append("xmajorgrids=true")
        elif xaxis.get("showgrid") is False:
            options.append("xmajorgrids=false")

        # Y-axis
        yaxis = layout.get("yaxis") or {}
        ytitle = yaxis.get("title")
        if isinstance(ytitle, dict):
            ytitle_text = ytitle.get("text", "")
        else:
            ytitle_text = str(ytitle) if ytitle is not None else ""
        if ytitle_text:
            options.append(f"ylabel={{{escape_tex(ytitle_text)}}}")

        if yaxis.get("type") == "log":
            options.append("ymode=log")

        yrange = yaxis.get("range")
        if yrange and isinstance(yrange, (list, tuple)) and len(yrange) == 2:
            options.append(f"ymin={yrange[0]}")
            options.append(f"ymax={yrange[1]}")

        if yaxis.get("showgrid") is True:
            options.append("ymajorgrids=true")
        elif yaxis.get("showgrid") is False:
            options.append("ymajorgrids=false")

        # Size
        width = layout.get("width")
        height = layout.get("height")
        if width and isinstance(width, (int, float)):
            options.append(f"width={width / 50.0:.1f}cm")
        if height and isinstance(height, (int, float)):
            options.append(f"height={height / 50.0:.1f}cm")

        # Legend position
        if layout.get("showlegend") is False:
            options.append("legend pos=none")

        return options

    def to_tikz(
        self,
        fig: Any,
        filename: Optional[str] = None,
        standalone: bool = False,
        tsv_threshold: int = 500,
    ) -> str:
        """
        Convert Plotly figure to LaTeX/TikZ PGFPlots code.

        Parameters:
        -----------
        fig : Figure or dict
            Plotly figure object or figure dictionary.
        filename : str, optional
            If provided, save the TikZ code (and TSV data files if needed) to this file path.
        standalone : bool, default False
            If True, generate a complete compilable LaTeX document.
        tsv_threshold : int, default 500
            Threshold of data points above which trace data is exported to external TSV file.

        Returns:
        --------
        str
            Generated LaTeX/TikZ code string.
        """
        if not isinstance(self, PlotlyToTikz):
            # Supports calling PlotlyToTikz.to_tikz(fig, ...) directly
            return PlotlyToTikz().to_tikz(
                fig, filename=filename, standalone=standalone, tsv_threshold=tsv_threshold
            )

        traces_data, layout_data = self._parse_figure(fig)
        axis_options = self._build_axis_options(layout_data)

        # Determine TSV file prefix and directory
        if filename:
            base_dir = os.path.dirname(filename)
            base_name = os.path.splitext(os.path.basename(filename))[0]
            tsv_prefix = base_name
        else:
            base_dir = ""
            tsv_prefix = "data"

        processed_traces = []
        extra_packages = set()
        pgfplots_libraries = set()

        for idx, trace in enumerate(traces_data):
            trace_type = trace.get("type", "scatter")
            handler = self.registry.get_handler(trace_type)
            trace_info = handler.process(
                trace,
                trace_index=idx,
                tsv_threshold=tsv_threshold,
                tsv_prefix=tsv_prefix,
            )

            extra_packages.update(trace_info.get("packages", set()))
            pgfplots_libraries.update(trace_info.get("libraries", set()))

            # Save TSV file if threshold exceeded
            if trace_info["data_type"] == "tsv" and trace_info["tsv_content"]:
                tsv_filename = trace_info["tsv_filename"]
                tsv_filepath = os.path.join(base_dir, tsv_filename) if base_dir else tsv_filename
                if base_dir:
                    os.makedirs(base_dir, exist_ok=True)
                with open(tsv_filepath, "w", encoding="utf-8") as f:
                    f.write(trace_info["tsv_content"])

            processed_traces.append(trace_info)

        axis_template = self.env.get_template("default_axis.tex")
        axis_code = axis_template.render(
            axis_options=axis_options,
            traces=processed_traces,
        )

        if standalone:
            standalone_template = self.env.get_template("standalone.tex")
            output_code = standalone_template.render(
                axis_code=axis_code,
                extra_packages=sorted(list(extra_packages)),
                pgfplots_libraries=sorted(list(pgfplots_libraries)),
            )
        else:
            preamble_lines = [
                "% Required Preamble:",
                "% \\usepackage{tikz}",
                "% \\usepackage{pgfplots}",
                "% \\pgfplotsset{compat=1.18}",
            ]
            for pkg in sorted(list(extra_packages)):
                preamble_lines.append(f"% \\usepackage{{{pkg}}}")
            for lib in sorted(list(pgfplots_libraries)):
                preamble_lines.append(f"% \\usepgfplotslibrary{{{lib}}}")

            preamble_str = "\n".join(preamble_lines)
            output_code = f"{preamble_str}\n{axis_code}"

        if filename:
            if base_dir:
                os.makedirs(base_dir, exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(output_code)

        return output_code


def to_tikz(
    fig: Any,
    filename: Optional[str] = None,
    standalone: bool = False,
    tsv_threshold: int = 500,
) -> str:
    """Convert Plotly figure to LaTeX/TikZ PGFPlots code."""
    converter = PlotlyToTikz()
    return converter.to_tikz(fig, filename=filename, standalone=standalone, tsv_threshold=tsv_threshold)
