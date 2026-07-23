"""Unit tests for Matplotlib to TikZ conversion in plotikz."""

import unittest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from plotikz import to_tikz, MatplotlibToTikz


class TestMatplotlibConverter(unittest.TestCase):
    def test_line_plot_conversion(self):
        fig, ax = plt.subplots()
        x = np.linspace(0, 10, 20)
        y = np.sin(x)
        ax.plot(x, y, label="Sin Wave", color="red", linestyle="--", linewidth=2)
        ax.set_title("Matplotlib Sine Test")
        ax.set_xlabel("X Axis")
        ax.set_ylabel("Y Axis")

        tikz_code = to_tikz(fig, standalone=False)
        plt.close(fig)

        self.assertIn(r"\begin{tikzpicture}", tikz_code)
        self.assertIn(r"\begin{axis}[", tikz_code)
        self.assertIn("title={Matplotlib Sine Test}", tikz_code)
        self.assertIn("xlabel={X Axis}", tikz_code)
        self.assertIn("ylabel={Y Axis}", tikz_code)
        self.assertIn(r"\addplot+", tikz_code)
        self.assertIn("dashed", tikz_code)
        self.assertIn("line width=2pt", tikz_code)

    def test_scatter_plot_conversion(self):
        fig, ax = plt.subplots()
        x = [1, 2, 3, 4]
        y = [10, 20, 15, 25]
        ax.scatter(x, y, color="blue", s=50, label="Scatter Dots")
        ax.set_title("Scatter Test")

        tikz_code = to_tikz(fig, standalone=False)
        plt.close(fig)

        self.assertIn(r"\begin{tikzpicture}", tikz_code)
        self.assertIn("title={Scatter Test}", tikz_code)
        self.assertIn(r"\addplot+", tikz_code)
        self.assertIn(r"\dataScatterDots", tikz_code)

    def test_from_pyplot_conversion(self):
        plt.figure()
        plt.plot([0, 1, 2], [3, 1, 4], label="Pyplot Line")
        plt.title("Pyplot Test")

        tikz_code = to_tikz(standalone=False)
        plt.close("all")

        self.assertIn(r"\begin{tikzpicture}", tikz_code)
        self.assertIn("title={Pyplot Test}", tikz_code)

    def test_unsupported_figure_type(self):
        with self.assertRaises(TypeError):
            to_tikz(12345)


if __name__ == "__main__":
    unittest.main()
