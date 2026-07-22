"""Main converter module for Plotly to TikZ/PGFPlots translation."""

import os
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from jinja2 import Environment, PackageLoader, FileSystemLoader, ChoiceLoader

from .registry import TraceRegistry, default_registry
from .utils import escape_tex, format_colorscale, clean_val, get_nice_ticks, format_color


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

        # Base directory and prefix for exported TSV files
        base_dir, tsv_prefix = self._get_tsv_paths(filename)

        # Process all traces through registered handlers
        processed_traces, data_tables, extra_packages, pgfplots_libraries = self._process_traces(
            traces_data, tsv_threshold=tsv_threshold, tsv_prefix=tsv_prefix, base_dir=base_dir
        )

        # Detect subplots and layout annotations
        subplot_groups, is_shared_x = self._detect_subplots(processed_traces, layout_data)
        annotations_list = self._extract_annotations(layout_data)

        # Build axis blocks for single-plot or multi-subplot figures
        axis_blocks, master_axis_options = self._build_axis_blocks(
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

            if trace_info.get("data_type") == "table_macro" and trace_info.get("table_content"):
                macro_name = self._make_descriptive_macro_name(trace.get("name"), idx, used_macro_names)
                trace_info["table_macro"] = macro_name
                indented_content = "\n".join(["    " + line for line in trace_info["table_content"].splitlines()])
                data_tables.append({
                    "macro_name": macro_name,
                    "content": indented_content,
                })

            if trace_info.get("data_type") == "tsv" and trace_info.get("tsv_content"):
                tsv_filename = trace_info["tsv_filename"]
                tsv_filepath = os.path.join(base_dir, tsv_filename) if base_dir else tsv_filename
                if base_dir:
                    os.makedirs(base_dir, exist_ok=True)
                with open(tsv_filepath, "w", encoding="utf-8") as f:
                    f.write(trace_info["tsv_content"])

            trace_info["raw_trace"] = trace
            processed_traces.append(trace_info)

        # Handle fillbetween (tonexty / tonextx) path naming
        if any(t.get("fill") in ("tonexty", "tonextx") for t in processed_traces):
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

        return processed_traces, data_tables, extra_packages, pgfplots_libraries

    def _normalize_axis_key(self, k: Any, axis_type: str = "y") -> str:
        """Normalize axis names ('y', 'y1', 'yaxis1' -> 'yaxis', 'y2' -> 'yaxis2')."""
        if not k:
            return f"{axis_type}axis"
        s = str(k).lower()
        if s in (axis_type, f"{axis_type}1", f"{axis_type}axis", f"{axis_type}axis1"):
            return f"{axis_type}axis"
        m = re.search(r"\d+", s)
        if m:
            return f"{axis_type}axis{m.group(0)}"
        return f"{axis_type}axis"

    def _detect_subplots(
        self, processed_traces: List[Dict[str, Any]], layout_data: Dict[str, Any]
    ) -> Tuple[Dict[Tuple[str, str], List[Dict[str, Any]]], bool]:
        """Group traces into subplots and check if x-axes are shared."""
        subplot_groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

        for t_info in processed_traces:
            raw_t = t_info.get("raw_trace", {})
            x_key = self._normalize_axis_key(raw_t.get("xaxis", "x"), "x")
            y_key = self._normalize_axis_key(raw_t.get("yaxis", "y"), "y")
            sp_key = (x_key, y_key)
            if sp_key not in subplot_groups:
                subplot_groups[sp_key] = []
            subplot_groups[sp_key].append(t_info)

        # Determine if x-axes are shared across subplots
        is_shared_x = len(subplot_groups) > 1
        if is_shared_x:
            # Check layout.xaxis2.matches or similar
            matches_x = any(
                isinstance(layout_data.get(k), dict) and layout_data[k].get("matches") in ("x", "xaxis")
                for k in layout_data if k.startswith("xaxis") and k != "xaxis"
            )
            if not matches_x:
                # Default to shared_x if all subplots share the same x axis or are stacked vertically
                x_keys = {key[0] for key in subplot_groups.keys()}
                is_shared_x = (len(x_keys) == 1) or len(subplot_groups) > 1

        return subplot_groups, is_shared_x

    def _build_axis_blocks(
        self,
        subplot_groups: Dict[Tuple[str, str], List[Dict[str, Any]]],
        is_shared_x: bool,
        layout_data: Dict[str, Any],
        processed_traces: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Build axis options and layout structures for single-plot or multi-subplot figures."""
        if len(subplot_groups) <= 1:
            master_opts = self._build_axis_options(layout_data, processed_traces)
            return [], master_opts

        axis_blocks = []
        num_sp = len(subplot_groups)
        raw_annotations = layout_data.get("annotations", [])

        # Calculate overall x-bounds across all traces if x-axis is shared
        global_x_min, global_x_max = None, None
        if is_shared_x:
            all_x_vals = []
            for t_info in processed_traces:
                raw_t = t_info.get("raw_trace", {})
                rx = raw_t.get("x", [])
                if hasattr(rx, "tolist"):
                    rx = rx.tolist()
                if isinstance(rx, (list, tuple)):
                    for v in rx:
                        cv = clean_val(v)
                        if cv is not None and isinstance(cv, (int, float)):
                            all_x_vals.append(float(cv))
            if all_x_vals:
                global_x_min = min(all_x_vals)
                global_x_max = max(all_x_vals)

        # Subplot height sizing
        if layout_data.get("height") and isinstance(layout_data["height"], (int, float)):
            h_total_cm = float(layout_data["height"]) / 50.0
            h_per_sp = max(3.2, round((h_total_cm / num_sp) - 0.6, 1))
        else:
            h_per_sp = 4.0

        sp_idx = 0
        for (x_key, y_key), sp_traces in subplot_groups.items():
            sp_idx += 1
            is_bottom = (sp_idx == num_sp)

            sub_layout = dict(layout_data)
            sub_layout["xaxis"] = dict(layout_data.get(x_key) or layout_data.get("xaxis") or {})
            sub_layout["yaxis"] = dict(layout_data.get(y_key) or layout_data.get("yaxis") or {})

            # Match subplot title from layout annotations
            sp_title = None
            if isinstance(raw_annotations, (list, tuple)):
                y_num = y_key.replace("yaxis", "")
                target_yref = f"y{y_num} domain" if y_num else "y domain"
                for ann in raw_annotations:
                    if isinstance(ann, dict) and (
                        ann.get("yref") == target_yref or ann.get("yref") == f"y{sp_idx} domain"
                    ):
                        sp_title = ann.get("text")
                        break

            if sp_title:
                sub_layout["title"] = sp_title
            elif sp_idx > 1 and "title" in sub_layout:
                sub_layout.pop("title", None)

            raw_sp_traces = [t.get("raw_trace", {}) for t in sp_traces]

            # Build options for this subplot
            sp_opts = self._build_axis_options(sub_layout, raw_sp_traces)

            # Apply shared x-axis ticks & limits
            if is_shared_x and global_x_min is not None and global_x_max is not None:
                nice_ticks = get_nice_ticks(global_x_min, global_x_max, max_ticks=5)
                ticks_str = ",".join([f"{v:g}" for v in nice_ticks])

                sp_opts = [
                    opt for opt in sp_opts
                    if not (opt.startswith("xmin=") or opt.startswith("xmax=") or opt.startswith("xtick="))
                ]
                sp_opts.append(f"xmin={global_x_min:g}")
                sp_opts.append(f"xmax={global_x_max:g}")
                sp_opts.append(f"xtick={{{ticks_str}}}")

                if not is_bottom:
                    # Hide tick labels on upper subplots in shared-x stack
                    sp_opts = [opt for opt in sp_opts if not opt.startswith("xlabel=")]
                    sp_opts.append("xticklabels=\\empty")

            # Height and width
            sp_opts = [opt for opt in sp_opts if not opt.startswith("height=")]
            sp_opts.append(f"height={h_per_sp:g}cm")
            if not any("width=" in opt for opt in sp_opts):
                sp_opts.append("width=14cm")

            # Position
            name = f"plot{sp_idx}"
            sp_opts.insert(0, f"name={name}")
            if sp_idx > 1:
                prev_name = f"plot{sp_idx - 1}"
                sp_opts.append(f"at={{({prev_name}.below south west)}}")
                sp_opts.append("anchor=north west")
                sp_opts.append("yshift=-0.8cm")

            axis_blocks.append({
                "axis_options": sp_opts,
                "axis_options_formatted": ",\n    ".join(sp_opts),
                "traces": sp_traces,
                "annotations": [],
            })

        return axis_blocks, []

    def _build_axis_options(self, layout: Dict[str, Any], traces: List[Dict[str, Any]]) -> List[str]:
        """Build list of PGFPlots axis options based on layout and trace types."""
        options = self._build_basic_layout_options(layout)

        trace_types = set()
        for t in traces:
            if isinstance(t, dict):
                ttype = t.get("type") or (t.get("raw_trace") or {}).get("type", "scatter")
                trace_types.add(ttype)

        if "heatmap" in trace_types or "contour" in trace_types:
            self._build_heatmap_contour_options(options, traces)
        elif "bar" in trace_types:
            self._build_bar_options(options, traces)
        elif "parcoords" in trace_types:
            self._build_parcoords_options(options, traces)
        else:
            self._build_scatter_options(options, traces)

        return options

    def _build_basic_layout_options(self, layout: Dict[str, Any]) -> List[str]:
        """Extract title, axes, layout dimensions, and legend options."""
        options = []

        # Title
        title = layout.get("title")
        title_text = title.get("text", "") if isinstance(title, dict) else (str(title) if title is not None else "")
        if title_text:
            options.append(f"title={{{escape_tex(title_text)}}}")

        # X-Axis
        xaxis = layout.get("xaxis") or {}
        xtitle = xaxis.get("title")
        xtitle_text = xtitle.get("text", "") if isinstance(xtitle, dict) else (str(xtitle) if xtitle is not None else "")
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

        # Y-Axis
        yaxis = layout.get("yaxis") or {}
        ytitle = yaxis.get("title")
        ytitle_text = ytitle.get("text", "") if isinstance(ytitle, dict) else (str(ytitle) if ytitle is not None else "")
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

        # Dimensions & Legend
        width = layout.get("width")
        height = layout.get("height")
        if width and isinstance(width, (int, float)):
            options.append(f"width={width / 50.0:.1f}cm")
        if height and isinstance(height, (int, float)):
            options.append(f"height={height / 50.0:.1f}cm")
        if layout.get("showlegend") is False:
            options.append("legend pos=none")

        return options

    def _build_heatmap_contour_options(self, options: List[str], traces: List[Dict[str, Any]]) -> None:
        """Add PGFPlots options for Heatmap and Contour plots."""
        if not any("view=" in opt for opt in options):
            options.append("view={0}{90}")
        if not any("colorbar" in opt for opt in options):
            options.append("colorbar")
        if not any("enlargelimits" in opt for opt in options):
            options.append("enlargelimits=false")
        if not any("axis on top" in opt for opt in options):
            options.append("axis on top")

        for t in traces:
            raw_t = t.get("raw_trace") or t
            t_type = raw_t.get("type") or t.get("type")
            if not isinstance(raw_t, dict) or t_type not in ("heatmap", "contour"):
                continue

            raw_z = raw_t.get("z", [])
            if hasattr(raw_z, "tolist"):
                raw_z = raw_z.tolist()

            z_vals = []
            if raw_z and isinstance(raw_z, list):
                for r in raw_z:
                    if hasattr(r, "tolist"):
                        r = r.tolist()
                    if isinstance(r, list):
                        for v in r:
                            cv = clean_val(v)
                            if cv is not None and isinstance(cv, (int, float)):
                                z_vals.append(float(cv))

            if z_vals:
                z_min = raw_t.get("zmin") if raw_t.get("zmin") is not None else min(z_vals)
                z_max = raw_t.get("zmax") if raw_t.get("zmax") is not None else max(z_vals)
                if not any("point meta min" in opt for opt in options):
                    options.append(f"point meta min={z_min:g}")
                if not any("point meta max" in opt for opt in options):
                    options.append(f"point meta max={z_max:g}")

                if t_type in ("contour", "heatmap") and not any("colorbar style" in opt for opt in options):
                    ticks_nice = get_nice_ticks(z_min, z_max, max_ticks=5)
                    ticks_str = ",".join([f"{v:g}" for v in ticks_nice])
                    options.append(f"colorbar style={{ytick={{{ticks_str}}}}}")

            if t_type == "heatmap":
                self._add_heatmap_halfcell_bounds(options, raw_t, raw_z)

            cs_val = raw_t.get("colorscale")
            cm_opt, _ = format_colorscale(cs_val)
            if cm_opt and not any("colormap" in opt for opt in options):
                options.append(cm_opt)
            break

    def _add_heatmap_halfcell_bounds(self, options: List[str], t: Dict[str, Any], raw_z: List[Any]) -> None:
        """Calculate half-cell boundaries so matrix plot fills axis frame 100%."""
        raw_x = t.get("x")
        raw_y = t.get("y")
        if hasattr(raw_x, "tolist"):
            raw_x = raw_x.tolist()
        if hasattr(raw_y, "tolist"):
            raw_y = raw_y.tolist()

        num_rows = len(raw_z) if raw_z and isinstance(raw_z, list) else 1
        num_cols = len(raw_z[0]) if (raw_z and isinstance(raw_z, list) and isinstance(raw_z[0], list)) else 1

        is_x_num = bool(raw_x and all(isinstance(clean_val(v), (int, float)) for v in raw_x))
        is_y_num = bool(raw_y and all(isinstance(clean_val(v), (int, float)) for v in raw_y))

        if raw_x and not any("xtick=" in opt for opt in options):
            if is_x_num:
                dx = (float(raw_x[-1]) - float(raw_x[0])) / max(1, len(raw_x) - 1) if len(raw_x) > 1 else 1.0
                half_dx = dx / 2.0
                if not any("xmin=" in opt for opt in options):
                    options.append(f"xmin={float(raw_x[0]) - half_dx:g}")
                if not any("xmax=" in opt for opt in options):
                    options.append(f"xmax={float(raw_x[-1]) + half_dx:g}")
                xticks_str = ",".join([f"{clean_val(v):g}" for v in raw_x])
            else:
                if not any("xmin=" in opt for opt in options):
                    options.append("xmin=0.5")
                if not any("xmax=" in opt for opt in options):
                    options.append(f"xmax={num_cols + 0.5:g}")
                ticks = [str(i + 1) for i in range(len(raw_x))]
                labels = [escape_tex(str(v)) for v in raw_x]
                xticks_str = ",".join(ticks)
                options.append(f"xticklabels={{{','.join(labels)}}}")
            options.append(f"xtick={{{xticks_str}}}")

        if raw_y and not any("ytick=" in opt for opt in options):
            if is_y_num:
                dy = (float(raw_y[-1]) - float(raw_y[0])) / max(1, len(raw_y) - 1) if len(raw_y) > 1 else 1.0
                half_dy = dy / 2.0
                if not any("ymin=" in opt for opt in options):
                    options.append(f"ymin={float(raw_y[0]) - half_dy:g}")
                if not any("ymax=" in opt for opt in options):
                    options.append(f"ymax={float(raw_y[-1]) + half_dy:g}")
                yticks_str = ",".join([f"{clean_val(v):g}" for v in raw_y])
            else:
                if not any("ymin=" in opt for opt in options):
                    options.append("ymin=0.5")
                if not any("ymax=" in opt for opt in options):
                    options.append(f"ymax={num_rows + 0.5:g}")
                ticks = [str(i + 1) for i in range(len(raw_y))]
                labels = [escape_tex(str(v)) for v in raw_y]
                yticks_str = ",".join(ticks)
                options.append(f"yticklabels={{{','.join(labels)}}}")
            options.append(f"ytick={{{yticks_str}}}")

    def _build_bar_options(self, options: List[str], traces: List[Dict[str, Any]]) -> None:
        """Add PGFPlots options for Bar charts."""
        if not any("ybar" in opt or "xbar" in opt for opt in options):
            options.append("ybar")
        if not any("ymin=" in opt for opt in options):
            options.append("ymin=0")

        for t in traces:
            raw_t = t.get("raw_trace") or t
            if isinstance(raw_t, dict) and raw_t.get("type") == "bar":
                raw_x = raw_t.get("x", [])
                if hasattr(raw_x, "tolist"):
                    raw_x = raw_x.tolist()
                if raw_x and not any("xtick=" in opt for opt in options):
                    clean_ticks = []
                    for v in raw_x:
                        cv = clean_val(v)
                        if cv is not None:
                            clean_ticks.append(f"{cv:g}" if isinstance(cv, (int, float)) else f"{{{cv}}}")
                    if clean_ticks:
                        options.append(f"xtick={{{','.join(clean_ticks)}}}")
                break

    def _build_scatter_options(self, options: List[str], traces: List[Dict[str, Any]]) -> None:
        """Add PGFPlots options for Scatter plots."""
        # Scatter plots rely on PGFPlots automatic tick generation unless xtick is specified
        pass

    def _build_parcoords_options(self, options: List[str], traces: List[Dict[str, Any]]) -> None:
        """Add PGFPlots options for Parallel Coordinates plots."""
        options.append("xmajorgrids=true")
        options.append("grid style={solid, black!60, line width=0.8pt}")
        options.append("xticklabel style={rotate=30, anchor=north east, font=\\small}")

        if not any("ymin=" in opt for opt in options):
            options.append("ymin=0")
        if not any("ymax=" in opt for opt in options):
            options.append("ymax=1")

        for t in traces:
            raw_t = t.get("raw_trace") or t
            if isinstance(raw_t, dict) and raw_t.get("type") == "parcoords":
                dimensions = raw_t.get("dimensions", [])
                if dimensions and isinstance(dimensions, list):
                    labels = []
                    ticks = []
                    for idx, dim in enumerate(dimensions, start=1):
                        ticks.append(str(idx))
                        if isinstance(dim, dict):
                            labels.append(f"{{{escape_tex(str(dim.get('label', f'Dim {idx}')))}}}")
                        else:
                            labels.append(f"{{{f'Dim {idx}'}}}")

                    if ticks and not any(opt.startswith("xtick=") for opt in options):
                        options.append(f"xtick={{{','.join(ticks)}}}")
                        options.append(f"xticklabels={{{','.join(labels)}}}")

                    if not any("xmin=" in opt for opt in options):
                        options.append("xmin=1")
                    if not any("xmax=" in opt for opt in options):
                        options.append(f"xmax={len(dimensions)}")
                    if not any("enlargelimits=" in opt for opt in options):
                        options.append("enlargelimits=false")
                break

    def _extract_annotations(self, layout_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse layout annotations into formatted TikZ node entries."""
        annotations_list = []
        raw_annotations = layout_data.get("annotations", [])
        if isinstance(raw_annotations, (list, tuple)):
            for ann in raw_annotations:
                if not isinstance(ann, dict):
                    continue
                ax_val = clean_val(ann.get("x"))
                ay_val = clean_val(ann.get("y"))
                text_val = ann.get("text", "")
                if ax_val is not None and ay_val is not None and text_val:
                    bgcolor = ann.get("bgcolor")
                    bordercolor = ann.get("bordercolor")
                    style_opts = ["font=\\small"]
                    if bgcolor:
                        col_opt, _ = format_color(bgcolor)
                        if col_opt:
                            style_opts.append(col_opt.replace("color=", "fill="))
                    else:
                        style_opts.append("fill=yellow!30")
                    if bordercolor:
                        col_opt, _ = format_color(bordercolor)
                        if col_opt:
                            style_opts.append(col_opt.replace("color=", "draw="))
                    else:
                        style_opts.append("draw=black!70")
                    style_opts.append("rounded corners")
                    style_opts.append("anchor=west")
                    annotations_list.append({
                        "x": ax_val,
                        "y": ay_val,
                        "text": escape_tex(text_val),
                        "style": ", ".join(style_opts),
                    })
        return annotations_list

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
