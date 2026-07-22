"""
Contour Plot Example using plotikz.

Demonstrates converting Plotly Contour traces (2D contour maps with lines and filled levels)
to PGFPlots contour plots.
Saves both LaTeX (.tex) and interactive Plotly HTML (.html) for comparison.
"""

import plotly.graph_objects as go
from plotikz import to_tikz


def main():
    z_data = [
        [10.0, 10.5, 12.0, 14.0],
        [15.0, 21.5, 23.0, 26.0],
        [20.0, 25.0, 31.0, 35.0],
        [25.0, 30.0, 38.0, 42.0],
    ]

    fig = go.Figure(
        data=[
            go.Contour(
                z=z_data,
                x=[1, 2, 3, 4],
                y=[1, 2, 3, 4],
                contours=dict(showlines=True, showlabels=True),
                line=dict(color="black"),
            )
        ],
        layout=go.Layout(
            title="Contour Plot Example",
            xaxis=dict(title="X Position"),
            yaxis=dict(title="Y Position"),
        ),
    )

    # Save LaTeX/TikZ file
    tex_filename = "contour_plot.tex"
    tikz_code = to_tikz(fig, filename=tex_filename, standalone=True)
    print(f"Generated LaTeX TikZ: '{tex_filename}'")

    # Save HTML file for comparison
    html_filename = "contour_plot.html"
    fig.write_html(html_filename)
    print(f"Generated Plotly HTML: '{html_filename}'")

    print("\nGenerated TikZ Code Preview:")
    print(tikz_code[:400] + "...\n")


if __name__ == "__main__":
    main()
