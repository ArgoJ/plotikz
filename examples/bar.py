"""
Bar Chart Example using plotikz.

Demonstrates converting Plotly Bar traces to PGFPlots bar charts.
Saves both LaTeX (.tex) and interactive Plotly HTML (.html) for comparison.
"""

import plotly.graph_objects as go
from plotikz import to_tikz


def main():
    fig = go.Figure(
        data=[
            go.Bar(
                x=[1, 2, 3, 4],
                y=[25, 40, 30, 55],
                name="Group 1",
                marker=dict(color="#2ca02c"),
            ),
            go.Bar(
                x=[1, 2, 3, 4],
                y=[15, 30, 45, 35],
                name="Group 2",
                marker=dict(color="#d62728"),
            ),
        ],
        layout=go.Layout(
            title="Bar Chart Example",
            xaxis=dict(title="Category / Quarter"),
            yaxis=dict(title="Sales (kEUR)"),
        ),
    )

    # Save LaTeX/TikZ file
    tex_filename = "bar_chart.tex"
    tikz_code = to_tikz(fig, filename=tex_filename, standalone=True)
    print(f"Generated LaTeX TikZ: '{tex_filename}'")

    # Save HTML file for comparison
    html_filename = "bar_chart.html"
    fig.write_html(html_filename)
    print(f"Generated Plotly HTML: '{html_filename}'")

    print("\nGenerated TikZ Code Preview:")
    print(tikz_code[:400] + "...\n")


if __name__ == "__main__":
    main()
