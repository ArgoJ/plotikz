"""
Heatmap Example using plotikz.

Demonstrates converting Plotly Heatmap 2D matrix traces to PGFPlots matrix plots.
Saves both LaTeX (.tex) and interactive Plotly HTML (.html) for comparison.
"""

import plotly.graph_objects as go
from plotikz import to_tikz


def main():
    z_data = [
        [10, 20, 30, 40],
        [20, 50, 80, 50],
        [30, 80, 100, 70],
        [40, 50, 70, 90],
    ]

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=z_data,
                x=[1, 2, 3, 4],
                y=[1, 2, 3, 4],
                colorscale="Viridis",
            )
        ],
        layout=go.Layout(
            title="Heatmap Matrix Plot Example",
            xaxis=dict(title="X Dimension"),
            yaxis=dict(title="Y Dimension"),
        ),
    )

    # Save LaTeX/TikZ file
    tex_filename = "heatmap_plot.tex"
    tikz_code = to_tikz(fig, filename=tex_filename, standalone=True)
    print(f"Generated LaTeX TikZ: '{tex_filename}'")

    # Save HTML file for comparison
    html_filename = "heatmap_plot.html"
    fig.write_html(html_filename)
    print(f"Generated Plotly HTML: '{html_filename}'")

    print("\nGenerated TikZ Code Preview:")
    print(tikz_code[:400] + "...\n")


if __name__ == "__main__":
    main()
