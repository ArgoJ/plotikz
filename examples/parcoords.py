"""
Parallel Coordinates (Parcoords) Plot Example using plotikz.

Demonstrates converting Plotly Parcoords traces with multiple dimensions,
custom axis ranges, and dimension labels to TikZ/PGFPlots.
Saves both LaTeX (.tex) and interactive Plotly HTML (.html) for comparison.
"""

import plotly.graph_objects as go
from plotikz import to_tikz


def main():
    fig = go.Figure(
        data=[
            go.Parcoords(
                line=dict(color="#1f77b4"),
                dimensions=[
                    dict(range=[1, 5], label="Sepal Length", values=[2.5, 3.0, 4.8, 1.2]),
                    dict(range=[0, 4], label="Sepal Width", values=[1.2, 2.1, 3.5, 0.8]),
                    dict(range=[1, 7], label="Petal Length", values=[1.5, 4.2, 6.1, 2.0]),
                    dict(range=[0, 3], label="Petal Width", values=[0.2, 1.3, 2.5, 0.4]),
                ],
                name="Iris Sample",
            )
        ],
        layout=go.Layout(title="Parallel Coordinates Plot Example"),
    )

    # Save LaTeX/TikZ file
    tex_filename = "parcoords_plot.tex"
    tikz_code = to_tikz(fig, filename=tex_filename, standalone=True)
    print(f"Generated LaTeX TikZ: '{tex_filename}'")

    # Save HTML file for comparison
    html_filename = "parcoords_plot.html"
    fig.write_html(html_filename)
    print(f"Generated Plotly HTML: '{html_filename}'")

    print("\nGenerated TikZ Code Preview:")
    print(tikz_code[:400] + "...\n")


if __name__ == "__main__":
    main()
