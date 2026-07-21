"""
Example usage script for plotikz.

This script demonstrates converting Plotly figures to LaTeX/TikZ code:
1. As a TikZ snippet (for embedding into an existing LaTeX document).
2. As a standalone compilable LaTeX document (.tex).
3. With large dataset export to TSV.
"""

import plotly.graph_objects as go
from plotikz import to_tikz, PlotlyToTikz


def run_examples():
    print("=== Example 1: Basic Scatter Plot to Snippet ===")
    fig1 = go.Figure(
        data=[
            go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[10, 15, 13, 17, 22],
                mode="lines+markers",
                name="Experiment A",
                line=dict(color="#1f77b4", dash="dash", width=2),
                marker=dict(symbol="circle", size=8),
            ),
            go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[16, 5, 11, 9, 13],
                mode="lines",
                name="Experiment B",
                line=dict(color="red", dash="solid"),
            ),
        ],
        layout=go.Layout(
            title="Experimental Data Comparison",
            xaxis=dict(title="Time (s)"),
            yaxis=dict(title="Response (mV)"),
        ),
    )

    snippet = to_tikz(fig1, standalone=False)
    print(snippet)
    print("\n" + "=" * 50 + "\n")

    print("=== Example 2: Standalone LaTeX Document Output ===")
    standalone_doc = to_tikz(fig1, standalone=True)
    print(standalone_doc)
    print("\n" + "=" * 50 + "\n")

    print("=== Example 3: Large Dataset Exporting to TSV ===")
    # Generate 1000 points
    import numpy as np

    x_vals = np.linspace(0, 10, 1000)
    y_vals = np.sin(x_vals)

    fig_large = go.Figure(
        data=[
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                name="Sine Wave",
            )
        ],
        layout=go.Layout(
            title="High Resolution Sine Wave",
            xaxis=dict(title="x"),
            yaxis=dict(title="sin(x)"),
        ),
    )

    # Save to file 'large_plot.tex' (TSV data will be exported alongside as 'large_plot_trace_0.tsv')
    tex_code = to_tikz(fig_large, filename="large_plot.tex", standalone=True, tsv_threshold=500)
    print("Generated 'large_plot.tex' and associated TSV file!")


if __name__ == "__main__":
    run_examples()
