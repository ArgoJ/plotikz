# plotikz Examples

This directory contains standalone Python example scripts demonstrating how to convert various Plotly figure types into clean LaTeX/TikZ PGFPlots code using `plotikz`.

Each example script exports both:
1. **`.tex` file**: Standalone LaTeX document containing the generated TikZ/PGFPlots code.
2. **`.html` file**: Interactive Plotly HTML file for visual side-by-side comparison.

## Available Examples

- **[scatter.py](scatter.py)**: Line and marker scatter plots (`go.Scatter`), line styling, dashes, markers, custom colors (`scatter_plot.tex` & `scatter_plot.html`).
- **[bar.py](bar.py)**: Categorical vertical bar charts (`go.Bar`) (`bar_chart.tex` & `bar_chart.html`).
- **[heatmap.py](heatmap.py)**: 2D matrix plots / heatmaps (`go.Heatmap`) (`heatmap_plot.tex` & `heatmap_plot.html`).
- **[contour.py](contour.py)**: 2D contour maps with levels and labels (`go.Contour`) (`contour_plot.tex` & `contour_plot.html`).
- **[parcoords.py](parcoords.py)**: Parallel Coordinates plots (`go.Parcoords`) with normalized axes and dimension labels (`parcoords_plot.tex` & `parcoords_plot.html`).

## Running Examples

To run an individual example:

```bash
python examples/scatter.py
python examples/bar.py
python examples/heatmap.py
python examples/contour.py
python examples/parcoords.py
```

To run all examples at once:

```bash
python examples/run_all.py
```
