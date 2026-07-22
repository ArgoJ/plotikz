"""
Scatter Plot Example using plotikz.

Demonstrates converting Plotly Scatter, Scattergl, and Scatter3d traces
with line styles, markers, custom colors, and legend entries to TikZ/PGFPlots.
Saves both LaTeX (.tex) and interactive Plotly HTML (.html) for comparison.
"""

import plotly.graph_objects as go
from plotikz import to_tikz


def main():
    fig = go.Figure(
        data=[
            go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[10, 15, 13, 17, 22],
                mode="lines+markers",
                name="Measurement A",
                line=dict(color="#1f77b4", dash="dash", width=2),
                marker=dict(symbol="circle", size=8),
            ),
            go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[16, 5, 11, 9, 13],
                mode="lines",
                name="Measurement B",
                line=dict(color="#ff7f0e", dash="solid", width=1.5),
            ),
            go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[7, 9, 12, 14, 19],
                mode="markers",
                name="Data Points",
                marker=dict(symbol="diamond", size=10, color="green"),
            ),
        ],
        layout=go.Layout(
            title="Scatter Plot Example",
            xaxis=dict(title="Time (s)"),
            yaxis=dict(title="Signal (mV)"),
        ),
    )

    # Save LaTeX/TikZ file
    tex_filename = "scatter_plot.tex"
    tikz_code = to_tikz(fig, filename=tex_filename, standalone=True)
    print(f"Generated LaTeX TikZ: '{tex_filename}'")

    # Save HTML file for comparison
    html_filename = "scatter_plot.html"
    fig.write_html(html_filename)
    print(f"Generated Plotly HTML: '{html_filename}'")

    print("\nGenerated TikZ Code Preview:")
    print(tikz_code[:400] + "...\n")


if __name__ == "__main__":
    main()
