# plotikz

`plotikz` is a Python library for converting Plotly figures into clean LaTeX / TikZ PGFPlots code. It supports both standalone compilable `.tex` documents and embedded TikZ snippets, as well as automatic TSV data file export for large datasets.

## Features

- **Supported Trace Types**:
  - `Scatter` / `Scattergl` (Lines, Markers, Dash styles, Colors)
  - `Bar` (Categorical Bar Charts)
  - `Heatmap` (2D Matrix plots with colormaps)
  - `Contour` (Filled contour lines and level labels)
  - `Parcoords` (Parallel Coordinates plots with multi-dimension scaling)
- **Flexible Export**: Generate standalone LaTeX documents or raw `\begin{tikzpicture}` snippets.
- **Large Dataset Support**: Automatically exports large data arrays to external TSV files when point count exceeds a configurable threshold.
- **Extensible Architecture**: Modular trace handler registry pattern.

## Quickstart

```python
import plotly.graph_objects as go
from plotikz import to_tikz

# 1. Create a Plotly Figure
fig = go.Figure(
    data=[
        go.Scatter(
            x=[1, 2, 3, 4],
            y=[10, 15, 13, 17],
            mode="lines+markers",
            name="Experiment A",
            line=dict(color="#1f77b4", dash="dash"),
        )
    ],
    layout=go.Layout(title="Sample Plot", xaxis=dict(title="X"), yaxis=dict(title="Y")),
)

# 2. Convert to LaTeX/TikZ code
tikz_code = to_tikz(fig, filename="output.tex", standalone=True)
```

## Examples

The [`examples/`](examples/README.md) directory contains complete example scripts for each supported plot type:

- [`examples/scatter.py`](examples/scatter.py) - Line & Marker Scatter plots
- [`examples/bar.py`](examples/bar.py) - Bar charts
- [`examples/heatmap.py`](examples/heatmap.py) - Heatmaps
- [`examples/contour.py`](examples/contour.py) - Contour plots
- [`examples/parcoords.py`](examples/parcoords.py) - Parallel Coordinates plots

Each example generates both a LaTeX TikZ file (`.tex`) and an interactive Plotly HTML file (`.html`) for visual comparison.

Run all examples:
```bash
PYTHONPATH=src python examples/run_all.py
```

## License

MIT