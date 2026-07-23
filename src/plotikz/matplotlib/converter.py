"""Main converter class and functions for Matplotlib figures and PyPlot."""

from typing import Any, Optional
import matplotlib.pyplot as plt

from ..plotly.converter import PlotlyToTikz
from .translator import figure_to_plotikz_data


class MatplotlibToTikz:
    """Converter for Matplotlib figures and PyPlot axes to LaTeX/TikZ PGFPlots code."""

    def __init__(self):
        self._plotly_converter = PlotlyToTikz()

    def to_tikz(
        self,
        fig: Any,
        filename: Optional[str] = None,
        standalone: bool = False,
        tsv_threshold: int = 500,
        **kwargs,
    ) -> str:
        """
        Convert Matplotlib Figure or Axes to LaTeX/TikZ PGFPlots code.

        Parameters:
        -----------
        fig : Figure or Axes
            Matplotlib Figure or Axes object.
        filename : str, optional
            If provided, save TikZ code (and TSV data files if needed) to this file path.
        standalone : bool, default False
            If True, generate a complete compilable LaTeX document.
        tsv_threshold : int, default 500
            Threshold of data points above which trace data is exported to external TSV file.
        **kwargs :
            Additional plot-specific configuration kwargs.

        Returns:
        --------
        str
            Generated LaTeX/TikZ code string.
        """
        traces, layout = figure_to_plotikz_data(fig)
        fig_dict = {"data": traces, "layout": layout}

        return self._plotly_converter.to_tikz(
            fig_dict, filename=filename, standalone=standalone, tsv_threshold=tsv_threshold, **kwargs
        )


def matplotlib_to_tikz(
    fig: Any,
    filename: Optional[str] = None,
    standalone: bool = False,
    tsv_threshold: int = 500,
    **kwargs,
) -> str:
    """Explicit converter for Matplotlib Figure or Axes object."""
    return MatplotlibToTikz().to_tikz(
        fig, filename=filename, standalone=standalone, tsv_threshold=tsv_threshold, **kwargs
    )


def from_pyplot(
    filename: Optional[str] = None,
    standalone: bool = False,
    tsv_threshold: int = 500,
    **kwargs,
) -> str:
    """Explicit converter for active Matplotlib PyPlot figure (plt.gcf())."""
    fig = plt.gcf()
    return matplotlib_to_tikz(fig, filename=filename, standalone=standalone, tsv_threshold=tsv_threshold, **kwargs)