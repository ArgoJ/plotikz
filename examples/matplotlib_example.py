"""Example demonstrating Matplotlib figure conversion to TikZ using plotikz."""

import matplotlib.pyplot as plt
import numpy as np
from plotikz import to_tikz


def main():
    # 1. Convert an explicit Matplotlib Figure
    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.linspace(0, 2 * np.pi, 50)
    ax.plot(x, np.sin(x), label="Sin", color="#1f77b4", linestyle="-", linewidth=2)
    ax.plot(x, np.cos(x), label="Cos", color="#ff7f0e", linestyle="--", linewidth=2)
    ax.set_title("Matplotlib Sine and Cosine Waves")
    ax.set_xlabel("Angle [rad]")
    ax.set_ylabel("Value")
    ax.grid(True)
    ax.legend()

    tikz_code = to_tikz(fig, filename="matplotlib_figure.tex", standalone=True)
    plt.close(fig)
    print("Generated 'matplotlib_figure.tex'!")

    # 2. Convert active PyPlot figure (to_tikz with no figure argument converts plt.gcf())
    plt.figure()
    plt.scatter([1, 2, 3, 4], [10, 25, 15, 30], color="red", label="Scatter Points")
    plt.title("Matplotlib PyPlot Scatter")
    plt.xlabel("X Axis")
    plt.ylabel("Y Axis")

    tikz_code_pyplot = to_tikz(filename="matplotlib_pyplot.tex", standalone=True)
    plt.close("all")
    print("Generated 'matplotlib_pyplot.tex'!")


if __name__ == "__main__":
    main()
