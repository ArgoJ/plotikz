"""Example script converting Plotly summary band plot with fill='tonexty' to LaTeX TikZ/PGFPlots."""

import numpy as np
import plotly.graph_objects as go
from plotikz import to_tikz


def add_summary_band(
    fig: go.Figure,
    stacked: np.ndarray,
    steps: np.ndarray | None = None,
) -> None:
    """Add max/min envelope plus mean and median lines for stacked data."""
    if stacked.size == 0:
        return

    x = np.arange(stacked.shape[1]) if steps is None else np.asarray(steps)
    y_min = np.nanmin(stacked, axis=0)
    y_max = np.nanmax(stacked, axis=0)
    y_mean = np.nanmean(stacked, axis=0)
    y_median = np.nanmedian(stacked, axis=0)

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y_max,
            mode="lines",
            name="max",
            line=dict(color="red", width=2),
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y_min,
            mode="lines",
            name="min",
            line=dict(color="red", width=2),
            fill="tonexty",
            fillcolor="rgba(255,0,0,0.3)",
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y_mean,
            mode="lines",
            name="mean",
            line=dict(color="black", width=2, dash="dash"),
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y_median,
            mode="lines",
            name="median",
            line=dict(color="blue", width=2),
            showlegend=True,
        )
    )


def create_summary_band_example() -> go.Figure:
    np.random.seed(42)
    n_runs = 20
    n_steps = 26
    steps = np.arange(n_steps)

    # Generate synthetic trajectories matching user image trend
    data = []
    for _ in range(n_runs):
        base = -75 * np.exp(-steps / 10.0) + np.random.normal(0, 3, size=n_steps)
        data.append(base)

    stacked = np.array(data)

    fig = go.Figure()
    add_summary_band(fig, stacked, steps)
    fig.update_layout(
        title="Summary Band Plot Example",
        xaxis=dict(title=r"$k$"),
        yaxis=dict(title=r"$\Delta V_k$"),
    )
    return fig


def main() -> None:
    fig = create_summary_band_example()

    # Generate TikZ output
    tikz_code = to_tikz(fig, filename="summary_band_plot.tex", standalone=True)
    print("Generated LaTeX TikZ: 'summary_band_plot.tex'")

    # Save HTML for visual verification
    fig.write_html("summary_band_plot.html")
    print("Generated Plotly HTML: 'summary_band_plot.html'")

    print("\nGenerated TikZ Code Preview:")
    print(tikz_code[:600] + "...\n")


if __name__ == "__main__":
    main()
