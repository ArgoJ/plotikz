"""Unit tests for plotikz library."""

import os
import tempfile
import unittest
import plotly.graph_objects as go

from plotikz import PlotlyToTikz, to_tikz, TraceHandler, default_registry, TraceRegistry


class TestPlotikzConverter(unittest.TestCase):
    def test_basic_scatter_conversion(self):
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=[1, 2, 3],
                    y=[4, 5, 6],
                    mode="lines+markers",
                    name="Test Line",
                    line=dict(color="#FF0000", dash="dash", width=2),
                )
            ],
            layout=go.Layout(
                title="Sample Plot",
                xaxis=dict(title="X Axis"),
                yaxis=dict(title="Y Axis"),
            ),
        )

        tikz_code = to_tikz(fig, standalone=False)

        self.assertIn(r"\begin{tikzpicture}", tikz_code)
        self.assertIn(r"\begin{axis}[", tikz_code)
        self.assertIn("title={Sample Plot}", tikz_code)
        self.assertIn("xlabel={X Axis}", tikz_code)
        self.assertIn("ylabel={Y Axis}", tikz_code)
        self.assertIn(r"\addplot+", tikz_code)
        self.assertIn("dashed", tikz_code)
        self.assertIn("line width=2pt", tikz_code)
        self.assertIn("color={rgb,255:red,255;green,0;blue,0}", tikz_code)
        self.assertIn("(1, 4) (2, 5) (3, 6)", tikz_code)
        self.assertIn(r"\addlegendentry{Test Line}", tikz_code)

    def test_standalone_mode(self):
        fig = go.Figure(data=[go.Scatter(x=[1, 2], y=[3, 4])])
        tex_code = to_tikz(fig, standalone=True)

        self.assertIn(r"\documentclass{article}", tex_code)
        self.assertIn(r"\usepackage{tikz}", tex_code)
        self.assertIn(r"\usepackage{pgfplots}", tex_code)
        self.assertIn(r"\pgfplotsset{compat=1.18}", tex_code)
        self.assertIn(r"\begin{document}", tex_code)
        self.assertIn(r"\end{document}", tex_code)

    def test_tsv_export_threshold(self):
        # Create trace with 100 points
        x = list(range(100))
        y = [i * 2 for i in x]
        fig = go.Figure(data=[go.Scatter(x=x, y=y)])

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "plot.tex")
            # Set threshold to 50 so 100 points triggers TSV mode
            tex_code = to_tikz(fig, filename=out_file, tsv_threshold=50)

            tsv_file = os.path.join(tmpdir, "plot_trace_0.tsv")
            self.assertTrue(os.path.exists(out_file))
            self.assertTrue(os.path.exists(tsv_file))
            self.assertIn("table [x=x, y=y, col sep=tab] {plot_trace_0.tsv}", tex_code)

            with open(tsv_file, "r", encoding="utf-8") as f:
                tsv_content = f.read()
                self.assertIn("x\ty", tsv_content)
                self.assertIn("0\t0", tsv_content)

    def test_plotly_dict_input(self):
        fig_dict = {
            "data": [{"type": "scatter", "x": [10, 20], "y": [30, 40], "mode": "markers"}],
            "layout": {"title": "Dict Figure"},
        }
        tikz_code = to_tikz(fig_dict)
        self.assertIn("only marks", tikz_code)
        self.assertIn("title={Dict Figure}", tikz_code)
        self.assertIn("(10, 30) (20, 40)", tikz_code)

    def test_bar_chart_conversion(self):
        fig = go.Figure(data=[go.Bar(x=[1, 2, 3], y=[10, 20, 30], name="Bar Trace")])
        tikz_code = to_tikz(fig)
        self.assertIn("ybar", tikz_code)
        self.assertIn(r"\addlegendentry{Bar Trace}", tikz_code)

    def test_heatmap_conversion(self):
        fig = go.Figure(
            data=[
                go.Heatmap(
                    z=[[1, 20, 30], [20, 1, 60], [30, 60, 1]],
                    x=["Monday", "Tuesday", "Wednesday"],
                    y=["Morning", "Afternoon", "Evening"],
                )
            ]
        )
        tikz_code = to_tikz(fig, standalone=True)
        self.assertIn("matrix plot", tikz_code)
        self.assertIn(r"\usepgfplotslibrary{colormaps}", tikz_code)

    def test_custom_handler_registry(self):
        class DummyCustomHandler(TraceHandler):
            def can_handle(self, trace_type: str) -> bool:
                return trace_type == "custom_type"

            def process(self, trace, trace_index, tsv_threshold=500, tsv_prefix=None):
                return {
                    "plot_cmd": r"\addplot+",
                    "options": ["custom_option"],
                    "options_str": "custom_option",
                    "data_type": "inline",
                    "inline_coords": "(0,0) (1,1)",
                    "tsv_filename": "",
                    "tsv_content": "",
                    "legend_entry": "Custom",
                    "packages": set(),
                    "libraries": set(),
                    "x_col": "x",
                    "y_col": "y",
                }

        registry = TraceRegistry()
        registry.register(DummyCustomHandler())
        converter = PlotlyToTikz(registry=registry)

        fig = {"data": [{"type": "custom_type"}]}
        tikz_code = converter.to_tikz(fig)
        self.assertIn("custom_option", tikz_code)
        self.assertIn(r"\addlegendentry{Custom}", tikz_code)

    def test_handlers_package_imports(self):
        from plotikz.handlers import (
            TraceHandler,
            ScatterHandler,
            BarHandler,
            HeatmapHandler,
            GenericHandler,
        )
        self.assertTrue(issubclass(ScatterHandler, TraceHandler))
        self.assertTrue(issubclass(BarHandler, TraceHandler))
        self.assertTrue(issubclass(HeatmapHandler, TraceHandler))
        self.assertTrue(issubclass(GenericHandler, TraceHandler))


if __name__ == "__main__":
    unittest.main()

