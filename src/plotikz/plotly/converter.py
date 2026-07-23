"""Main Plotly to TikZ/PGFPlots converter class and convenience function."""

import os
import re
from typing import Dict, Any, List, Optional, Tuple
from jinja2 import Environment, PackageLoader, FileSystemLoader, ChoiceLoader

from ..registry import TraceRegistry, default_registry
from .options_builder import build_axis_options
from .subplots import detect_subplots, build_axis_blocks
from .annotations import extract_annotations


class PlotlyToTikz:
    """Converter for Plotly figures to LaTeX/TikZ PGFPlots code."""

    def __init__(self, registry: Optional[TraceRegistry] = None):
        """Initialize converter with optional custom trace registry."""
        self.registry = registry or default_registry

        # Setup Jinja2 environment with LaTeX-safe delimiters
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
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
            If provided, save TikZ code (and TSV data files if needed) to this file path.
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
            return PlotlyToTikz().to_tikz(
                fig, filename=filename, standalone=standalone, tsv_threshold=tsv_threshold
            )

        traces_data, layout_data = self._parse_figure(fig)
        base_dir, tsv_prefix = self._get_tsv_paths(filename)

        # Process traces through registered handlers
        processed_traces, data_tables, extra_packages, pgfplots_libraries = self._process_traces(
            traces_data, tsv_threshold=tsv_threshold, tsv_prefix=tsv_prefix, base_dir=base_dir
        )

        # Ensure contour background images are drawn first (below scatter traces)
        self._sort_traces_by_layer(processed_traces)

        # Detect subplots and layout annotations
        subplot_groups, is_shared_x = detect_subplots(processed_traces, layout_data)
        annotations_list = extract_annotations(layout_data)

        # Build axis blocks for single-plot or multi-subplot figures
        axis_blocks, master_axis_options = build_axis_blocks(
            subplot_groups, is_shared_x, layout_data, processed_traces
        )

        # Render TikZ code using Jinja2 templates
        axis_template = self.env.get_template("default_axis.tex")
        if axis_blocks:
            axis_code = axis_template.render(
                axis_blocks=axis_blocks,
                data_tables=data_tables,
            )
        else:
            axis_options_formatted = ",\n    ".join(master_axis_options)
            axis_code = axis_template.render(
                axis_options=master_axis_options,
                axis_options_formatted=axis_options_formatted,
                traces=processed_traces,
                data_tables=data_tables,
                annotations=annotations_list,
            )

        output_code = self._render_document(
            axis_code, standalone=standalone, extra_packages=extra_packages, pgfplots_libraries=pgfplots_libraries
        )

        if filename:
            if base_dir:
                os.makedirs(base_dir, exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(output_code)

        return output_code

    # -------------------------------------------------------------------------
    # Figure Parsing & Setup
    # -------------------------------------------------------------------------

    def _parse_figure(self, fig: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Normalize input figure into list of trace dicts and layout dict."""
        traces = []
        layout = {}

        if hasattr(fig, "data") and hasattr(fig, "layout"):
            traces = fig.data
            layout = fig.layout
            if hasattr(layout, "to_plotly_json"):
                layout = layout.to_plotly_json()
            elif hasattr(layout, "to_dict"):
                layout = layout.to_dict()
        elif isinstance(fig, dict):
            traces = fig.get("data", [])
            layout = fig.get("layout", {})
        elif hasattr(fig, "to_dict"):
            fig_dict = fig.to_dict()
            traces = fig_dict.get("data", [])
            layout = fig_dict.get("layout", {})
        elif isinstance(fig, list):
            traces = fig
            layout = {}

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

    def _get_tsv_paths(self, filename: Optional[str]) -> Tuple[str, str]:
        """Determine base directory and filename prefix for exported TSV files."""
        if filename:
            base_dir = os.path.dirname(filename)
            base_name = os.path.splitext(os.path.basename(filename))[0]
            return base_dir, base_name
        return "", "data"

    def _sort_traces_by_layer(self, processed_traces: List[Dict[str, Any]]) -> None:
        """Ensure background graphics (e.g. \\addplot graphics) draw first."""
        def _sort_key(t):
            code = t.get("plot_code", "")
            return 0 if "\\addplot graphics" in code else 1

        processed_traces.sort(key=_sort_key)

    # -------------------------------------------------------------------------
    # Trace & Data Table Processing
    # -------------------------------------------------------------------------

    def _process_traces(
        self,
        traces_data: List[Dict[str, Any]],
        tsv_threshold: int,
        tsv_prefix: str,
        base_dir: str,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], set, set]:
        """Run trace handlers, write TSV files, format macro tables, and configure fillbetween."""
        processed_traces = []
        extra_packages = set()
        pgfplots_libraries = set()
        data_tables = []
        used_macro_names = set()

        for idx, trace in enumerate(traces_data):
            trace_type = trace.get("type", "scatter")
            handler = self.registry.get_handler(trace_type)
            try:
                trace_info = handler.process(
                    trace,
                    trace_index=idx,
                    tsv_threshold=tsv_threshold,
                    tsv_prefix=tsv_prefix,
                    base_dir=base_dir,
                )
            except TypeError:
                trace_info = handler.process(
                    trace,
                    trace_index=idx,
                    tsv_threshold=tsv_threshold,
                    tsv_prefix=tsv_prefix,
                )

            extra_packages.update(trace_info.get("packages", set()))
            pgfplots_libraries.update(trace_info.get("libraries", set()))

            # Single table macro
            if trace_info.get("data_type") == "table_macro" and trace_info.get("table_content"):
                macro_name = self._register_data_table(
                    trace.get("name"), idx, trace_info["table_content"], used_macro_names, data_tables
                )
                trace_info["table_macro"] = macro_name

            # Multiple extra table macros (e.g. contour level lines)
            if trace_info.get("extra_tables"):
                extra_plot_lines = []
                for item in trace_info["extra_tables"]:
                    hint = item.get("name_hint") or trace.get("name") or "Table"
                    macro_name = self._register_data_table(
                        hint, idx, item.get("table_content", ""), used_macro_names, data_tables
                    )
                    cmd = item.get("plot_cmd", "\\addplot+")
                    extra_plot_lines.append(f"{cmd} table {{{macro_name}}};")

                if trace_info.get("bg_cmd"):
                    extra_plot_lines.insert(0, trace_info["bg_cmd"])

                trace_info["plot_code"] = "\n    ".join(extra_plot_lines)
            elif trace_info.get("bg_cmd"):
                trace_info["plot_code"] = trace_info["bg_cmd"]

            # TSV export
            if trace_info.get("data_type") == "tsv" and trace_info.get("tsv_content"):
                self._write_tsv_file(base_dir, trace_info["tsv_filename"], trace_info["tsv_content"])

            trace_info["raw_trace"] = trace
            processed_traces.append(trace_info)

        # Handle fillbetween (tonexty / tonextx) path naming
        self._apply_fillbetween(processed_traces, pgfplots_libraries)

        return processed_traces, data_tables, extra_packages, pgfplots_libraries

    def _register_data_table(
        self,
        name_hint: Optional[str],
        trace_idx: int,
        raw_table_content: str,
        used_macro_names: set,
        data_tables: List[Dict[str, Any]],
    ) -> str:
        """Format table content with 4-space indentation and register a macro name."""
        macro_name = self._make_descriptive_macro_name(name_hint, trace_idx, used_macro_names)
        content_clean = raw_table_content.expandtabs(4)
        indented_content = "\n".join(["    " + line for line in content_clean.splitlines()])
        data_tables.append({
            "macro_name": macro_name,
            "content": indented_content,
        })
        return macro_name

    def _write_tsv_file(self, base_dir: str, tsv_filename: str, tsv_content: str) -> None:
        """Write TSV content to disk."""
        tsv_filepath = os.path.join(base_dir, tsv_filename) if base_dir else tsv_filename
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)
        with open(tsv_filepath, "w", encoding="utf-8") as f:
            f.write(tsv_content)

    def _apply_fillbetween(
        self, processed_traces: List[Dict[str, Any]], pgfplots_libraries: set
    ) -> None:
        """Configure fillbetween library and path names for tonexty / tonextx traces."""
        if not any(t.get("fill") in ("tonexty", "tonextx") for t in processed_traces):
            return

        pgfplots_libraries.add("fillbetween")
        prev_path_name = None
        for t_info in processed_traces:
            macro_name = t_info.get("table_macro")
            if macro_name:
                path_name = macro_name.lstrip("\\")
                opts = list(t_info.get("options", []))
                opts.insert(0, f"name path={path_name}")
                t_info["options"] = opts
                t_info["options_str"] = ", ".join(opts)

                if t_info.get("fill") in ("tonexty", "tonextx") and prev_path_name:
                    fill_opts = []
                    if t_info.get("fill_color_opt"):
                        fill_opts.append(t_info["fill_color_opt"])
                    if t_info.get("fill_opacity") is not None:
                        fill_opts.append(f"fill opacity={t_info['fill_opacity']}")
                    fill_opts.append("draw=none")
                    fill_opts_str = ", ".join(fill_opts)
                    t_info["fill_between_cmd"] = f"\\addplot[{fill_opts_str}] fill between[of={prev_path_name} and {path_name}];"
                prev_path_name = path_name

    @staticmethod
    def _make_descriptive_macro_name(trace_name: Optional[str], index: int, used_names: set) -> str:
        """Generate valid LaTeX control sequence macro name (e.g. \\dataTraceOne)."""
        words_map = {
            "0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four",
            "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"
        }
        if trace_name and isinstance(trace_name, str):
            cleaned = re.sub(r"[^a-zA-Z0-9]", " ", trace_name)
            words = [w.capitalize() for w in cleaned.split() if w]
            if words:
                safe_words = []
                for w in words:
                    safe_w = "".join([words_map[c] if c in words_map else c for c in w])
                    safe_words.append(safe_w)
                candidate = f"\\data{''.join(safe_words)}"
                idx = 1
                orig_cand = candidate
                while candidate in used_names:
                    candidate = f"{orig_cand}{idx}"
                    idx += 1
                used_names.add(candidate)
                return candidate

        number_words = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]
        if index < len(number_words):
            word = number_words[index]
        else:
            word = "".join([words_map[c] for c in str(index + 1)])

        candidate = f"\\dataTrace{word}"
        idx = 1
        while candidate in used_names:
            candidate = f"\\dataTrace{word}{idx}"
            idx += 1
        used_names.add(candidate)
        return candidate

    # -------------------------------------------------------------------------
    # Document Rendering
    # -------------------------------------------------------------------------

    def _render_document(
        self,
        axis_code: str,
        standalone: bool,
        extra_packages: set,
        pgfplots_libraries: set,
    ) -> str:
        """Render complete standalone LaTeX document or snippet with preamble comments."""
        if standalone:
            standalone_template = self.env.get_template("standalone.tex")
            return standalone_template.render(
                axis_code=axis_code,
                extra_packages=sorted(list(extra_packages)),
                pgfplots_libraries=sorted(list(pgfplots_libraries)),
            )

        preamble_lines = [
            "% Required Preamble:",
            "% \\usepackage{amsmath}",
            "% \\usepackage{tikz}",
            "% \\usepackage{pgfplots}",
            "% \\pgfplotsset{compat=1.18}",
        ]
        for pkg in sorted(list(extra_packages)):
            preamble_lines.append(f"% \\usepackage{{{pkg}}}")
        for lib in sorted(list(pgfplots_libraries)):
            preamble_lines.append(f"% \\usepgfplotslibrary{{{lib}}}")

        preamble_str = "\n".join(preamble_lines)
        return f"{preamble_str}\n{axis_code}"


def to_tikz(
    fig: Any,
    filename: Optional[str] = None,
    standalone: bool = False,
    tsv_threshold: int = 500,
) -> str:
    """Convenience module-level function to convert Plotly figure to TikZ."""
    return PlotlyToTikz().to_tikz(
        fig, filename=filename, standalone=standalone, tsv_threshold=tsv_threshold
    )
