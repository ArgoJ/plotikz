"""Example script converting 2D Contour plot with Viridis colormap and red dotted overlay curves to LaTeX TikZ/PGFPlots."""

import numpy as np
import plotly.graph_objects as go
from plotikz import to_tikz


def create_contour_overlay_example() -> go.Figure:
    x = np.linspace(-10, 10, 150)
    y = np.linspace(-10, 10, 150)
    X, Y = np.meshgrid(x, y)

    # 2D Energy landscape matching the provided screenshot
    Z = 5 * X**2 + 8 * X * Y + 5 * Y**2 + 50

    fig = go.Figure()

    # 1. 2D Contour background plot with Viridis colorbar and level lines
    fig.add_trace(
        go.Contour(
            z=Z,
            x=x,
            y=y,
            colorscale="Viridis",
            contours=dict(showlines=True),
            colorbar=dict(title=""),
        )
    )

    # 2. Red dotted overlay boundary curves
    curve_y = np.linspace(-10, 10, 100)
    curve_x1 = -0.5 * curve_y - 4.5
    curve_x2 = -0.5 * curve_y + 4.5

    fig.add_trace(
        go.Scatter(
            x=curve_x1,
            y=curve_y,
            mode="lines",
            line=dict(color="red", width=4, dash="dot"),
            name="Boundary 1",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=curve_x2,
            y=curve_y,
            mode="lines",
            line=dict(color="red", width=4, dash="dot"),
            name="Boundary 2",
            showlegend=False,
        )
    )

    fig.update_layout(
        title="Contour Plot with Red Dotted Overlay",
        xaxis=dict(title=r"$x$"),
        yaxis=dict(title=r"$v$"),
    )
    return fig


def main() -> None:
    fig = create_contour_overlay_example()

    # Generate TikZ code
    tikz_code = to_tikz(fig, filename="contour_overlay_plot.tex", standalone=True)
    print("Generated LaTeX TikZ: 'contour_overlay_plot.tex'")

    # Save HTML for visual comparison
    fig.write_html("contour_overlay_plot.html")
    print("Generated Plotly HTML: 'contour_overlay_plot.html'")

    print("\nGenerated TikZ Code Preview:")
    print(tikz_code[:600] + "...\n")


if __name__ == "__main__":
    main()
