"""
Master runner script for all plotikz examples.

Runs each figure example (scatter, bar, heatmap, contour, parcoords, matplotlib)
and outputs standalone LaTeX (.tex) and interactive Plotly HTML (.html) files
in the current working directory for comparison.
"""

from scatter import main as run_scatter
from bar import main as run_bar
from heatmap import main as run_heatmap
from contour import main as run_contour
from parcoords import main as run_parcoords
from summary_band import main as run_summary_band
from contour_overlay import main as run_contour_overlay
from lyapunov_landscape import main as run_lyapunov_landscape
from mpc_trajectories import main as run_mpc_trajectories
from matplotlib_example import main as run_matplotlib_example


def run_all():
    print("==========================================")
    print(" Running plotikz Example Suite")
    print("==========================================")

    print("\n[1/10] Running Scatter Plot Example...")
    run_scatter()

    print("\n[2/10] Running Bar Chart Example...")
    run_bar()

    print("\n[3/10] Running Heatmap Example...")
    run_heatmap()

    print("\n[4/10] Running Contour Plot Example...")
    run_contour()

    print("\n[5/10] Running Parallel Coordinates Example...")
    run_parcoords()

    print("\n[6/10] Running Summary Band Example...")
    run_summary_band()

    print("\n[7/10] Running Contour Overlay Example...")
    run_contour_overlay()

    print("\n[8/10] Running Lyapunov Landscape Example...")
    run_lyapunov_landscape()

    print("\n[9/10] Running MPC Trajectories Example...")
    run_mpc_trajectories()

    print("\n[10/10] Running Matplotlib Example...")
    run_matplotlib_example()

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
        ("matplotlib_figure.tex", "matplotlib_pyplot.tex"),
    ]
    for tex, other in pairs:
        print(f"  - {tex} | {other}")
    print("==========================================")


if __name__ == "__main__":
    run_all()
