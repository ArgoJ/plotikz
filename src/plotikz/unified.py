"""Unified entry point to_tikz for direct Plotly and Matplotlib figure objects."""

from typing import Any, Optional
import matplotlib.figure
import matplotlib.axes
import plotly.graph_objects as go

from .matplotlib import MatplotlibToTikz, from_pyplot
from .plotly import PlotlyToTikz


def to_tikz(
    fig: Any = None,
    filename: Optional[str] = None,
    standalone: bool = False,
    tsv_threshold: int = 500,
    **kwargs,
) -> str:
    """
    Convert a Plotly figure (go.Figure) or Matplotlib figure/axes to LaTeX/TikZ PGFPlots code.

    Parameters:
    -----------
    fig : Plotly Figure (go.Figure), Matplotlib Figure/Axes, or None (default: active PyPlot figure)
        The figure object to convert. If None, automatically converts the active PyPlot figure (plt.gcf()).
    filename : str, optional
        If provided, save TikZ code (and TSV data files if needed) to this file path.
    standalone : bool, default False
        If True, generate a complete compilable LaTeX document.
    tsv_threshold : int, default 500
        Threshold of data points above which trace data is exported to external TSV file.
    **kwargs :
        Additional plot-specific options passed down to PGFPlots builders (e.g. colorbar_ticks=5).

    Returns:
    --------
    str
        Generated LaTeX/TikZ code string.

    Raises:
    -------
    TypeError
        If fig is not a supported Plotly or Matplotlib figure type.
    """
    str_filename = str(filename) if filename is not None else None

    # 1. If fig is None, convert current active PyPlot figure (plt.gcf())
    if fig is None:
        return from_pyplot(
            filename=str_filename, standalone=standalone, tsv_threshold=tsv_threshold, **kwargs
        )

    # 2. Check for Matplotlib Figure or Axes object via isinstance
    if isinstance(fig, (matplotlib.figure.Figure, matplotlib.axes.Axes)):
        return MatplotlibToTikz().to_tikz(
            fig, filename=str_filename, standalone=standalone, tsv_threshold=tsv_threshold, **kwargs
        )

    # 3. Check for Plotly Figure object via isinstance
    if isinstance(fig, go.Figure):
        return PlotlyToTikz().to_tikz(
            fig, filename=str_filename, standalone=standalone, tsv_threshold=tsv_threshold, **kwargs
        )

    # 4. Unsupported object type
    raise TypeError(
        f"Unsupported figure type: '{type(fig).__name__}'. "
        "Expected a Plotly Figure (go.Figure) or Matplotlib Figure/Axes."
    )
