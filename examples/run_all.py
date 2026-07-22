"""
Master runner script for all plotikz examples.

Runs each figure example (scatter, bar, heatmap, contour, parcoords)
and outputs standalone LaTeX (.tex) and interactive Plotly HTML (.html) files
in the current working directory for comparison.
"""

import os

from scatter import main as run_scatter
from bar import main as run_bar
from heatmap import main as run_heatmap
from contour import main as run_contour
from parcoords import main as run_parcoords
from summary_band import main as run_summary_band
from contour_overlay import main as run_contour_overlay
from lyapunov_landscape import main as run_lyapunov_landscape
from mpc_trajectories import main as run_mpc_trajectories


def run_all():
    print("==========================================")
    print(" Running plotikz Example Suite")
    print("==========================================")

    print("\n[1/9] Running Scatter Plot Example...")
    run_scatter()

    print("\n[2/9] Running Bar Chart Example...")
    run_bar()

    print("\n[3/9] Running Heatmap Example...")
    run_heatmap()

    print("\n[4/9] Running Contour Plot Example...")
    run_contour()

    print("\n[5/9] Running Parallel Coordinates Example...")
    run_parcoords()

    print("\n[6/9] Running Summary Band Example...")
    run_summary_band()

    print("\n[7/9] Running Contour Overlay Example...")
    run_contour_overlay()

    print("\n[8/9] Running Lyapunov Landscape Example...")
    run_lyapunov_landscape()

    print("\n[9/9] Running MPC Trajectories Example...")
    run_mpc_trajectories()

    print("\n==========================================")
    print(" All examples completed successfully!")
    print(" Generated TeX & HTML files:")
    pairs = [
        ("scatter_plot.tex", "scatter_plot.html"),
        ("bar_chart.tex", "bar_chart.html"),
        ("heatmap_plot.tex", "heatmap_plot.html"),
        ("contour_plot.tex", "contour_plot.html"),
        ("parcoords_plot.tex", "parcoords_plot.html"),
        ("summary_band_plot.tex", "summary_band_plot.html"),
        ("contour_overlay_plot.tex", "contour_overlay_plot.html"),
        ("lyapunov_landscape_plot.tex", "lyapunov_landscape_plot.html"),
        ("mpc_trajectories_plot.tex", "mpc_trajectories_plot.html"),
    ]
    for tex, html in pairs:
        print(f"  - {tex} | {html}")
    print("==========================================")


if __name__ == "__main__":
    run_all()
