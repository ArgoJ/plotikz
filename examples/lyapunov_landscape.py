"""Example script converting a Lyapunov Landscape plot with many trajectories and annotations to LaTeX TikZ/PGFPlots."""

import numpy as np
import plotly.graph_objects as go
from plotikz import to_tikz


def create_lyapunov_landscape_example() -> go.Figure:
    x = np.linspace(-10, 10, 150)
    y = np.linspace(-10, 10, 150)
    X, Y = np.meshgrid(x, y)

    # Lyapunov energy landscape matching Image 1
    Z = 5 * X**2 + 8 * X * Y + 5 * Y**2 + 50

    fig = go.Figure()

    # 1. Background Contour Heatmap
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

    # 2. Add 40 phase space trajectory curves spiraling into (0,0)
    np.random.seed(42)
    t = np.linspace(0, 5, 80)
    for i in range(40):
        r0 = np.random.uniform(4, 12)
        theta0 = np.random.uniform(0, 2 * np.pi)
        
        r_t = r0 * np.exp(-0.8 * t)
        theta_t = theta0 + 2.5 * t
        
        x_traj = r_t * np.cos(theta_t)
        v_traj = r_t * np.sin(theta_t)
        
        # Smooth color palette for trajectories
        color = f"hsl({int((i * 15) % 360)}, 70%, 50%)"
        fig.add_trace(
            go.Scatter(
                x=x_traj,
                y=v_traj,
                mode="lines",
                line=dict(color=color, width=1.5),
                showlegend=False,
            )
        )

    # 3. Add Annotation Callout box as seen in Image 1
    fig.add_annotation(
        x=5.38,
        y=1.14,
        text=r"$(5.381996, 1.136293) \text{Run 12}$",
        showarrow=True,
        bgcolor="rgba(255, 235, 150, 0.9)",
        bordercolor="rgba(180, 150, 0, 1.0)",
    )

    fig.update_layout(
        title=r"Lyapunov Landscape ($x$ vs $v$)",
        xaxis=dict(title=r"$x$"),
        yaxis=dict(title=r"$v$"),
    )
    return fig


def main() -> None:
    fig = create_lyapunov_landscape_example()

    # Convert to TikZ
    tikz_code = to_tikz(fig, filename="lyapunov_landscape_plot.tex", standalone=True)
    print("Generated LaTeX TikZ: 'lyapunov_landscape_plot.tex'")

    # Save Plotly HTML
    fig.write_html("lyapunov_landscape_plot.html")
    print("Generated Plotly HTML: 'lyapunov_landscape_plot.html'")


if __name__ == "__main__":
    main()
