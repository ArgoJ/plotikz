"""Example script converting MPC Trajectories subplots to LaTeX TikZ/PGFPlots."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotikz import to_tikz


def create_mpc_trajectories_example() -> go.Figure:
    t = np.linspace(0, 4, 80)
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("State x(t)", "State v(t)", "Control u(t)"),
    )

    np.random.seed(42)
    for i in range(35):
        x0 = np.random.uniform(-10, 10)
        v0 = np.random.uniform(-10, 10)

        # Damped response trajectory
        x_traj = x0 * np.exp(-1.2 * t) * np.cos(2.5 * t)
        v_traj = v0 * np.exp(-1.2 * t) * np.sin(2.5 * t)
        u_traj = np.clip(-2.5 * x_traj - 1.2 * v_traj, -10, 10)

        color = f"hsl({int((i * 18) % 360)}, 75%, 45%)"

        # Row 1: State x
        fig.add_trace(
            go.Scatter(
                x=t,
                y=x_traj,
                mode="lines",
                line=dict(color=color, width=1.5),
                showlegend=False,
            ),
            row=1,
            col=1,
        )

        # Row 2: State v
        fig.add_trace(
            go.Scatter(
                x=t,
                y=v_traj,
                mode="lines",
                line=dict(color=color, width=1.5),
                showlegend=False,
            ),
            row=2,
            col=1,
        )

        # Row 3: Control u (Step plot hv)
        fig.add_trace(
            go.Scatter(
                x=t,
                y=u_traj,
                mode="lines",
                line=dict(color=color, width=1.5, shape="hv"),
                showlegend=False,
            ),
            row=3,
            col=1,
        )

    fig.update_layout(
        title="MPC Trajectories",
        height=800,
    )
    fig.update_xaxes(title_text=r"$t$", row=3, col=1)
    fig.update_yaxes(title_text=r"$x$", row=1, col=1)
    fig.update_yaxes(title_text=r"$v$", row=2, col=1)
    fig.update_yaxes(title_text=r"$u$", row=3, col=1)
    return fig


def main() -> None:
    fig = create_mpc_trajectories_example()

    # Convert to TikZ
    tikz_code = to_tikz(fig, filename="mpc_trajectories_plot.tex", standalone=True)
    print("Generated LaTeX TikZ: 'mpc_trajectories_plot.tex'")

    # Save Plotly HTML
    fig.write_html("mpc_trajectories_plot.html")
    print("Generated Plotly HTML: 'mpc_trajectories_plot.html'")


if __name__ == "__main__":
    main()
