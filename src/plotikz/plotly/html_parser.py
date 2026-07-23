"""HTML parser for plotikz.

Extracts Plotly figure data and layout from HTML files,
decoding base64 binary typed arrays (bdata) used by Plotly
for large numpy arrays.
"""

import base64
import json
import re
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


def decode_bdata(obj: Any) -> Any:
    """Recursively decode base64-encoded typed arrays (bdata) from Plotly HTML."""
    if isinstance(obj, dict) and "bdata" in obj and "dtype" in obj:
        try:
            raw = base64.b64decode(obj["bdata"])
            fmt_map = {
                "i1": "b", "u1": "B",
                "i2": "h", "u2": "H",
                "i4": "i", "u4": "I",
                "i8": "q", "u8": "Q",
                "f2": "e", "f4": "f", "f8": "d",
            }
            fmt_char = fmt_map.get(obj["dtype"], "f")
            count = len(raw) // struct.calcsize(fmt_char)
            return list(struct.unpack(f"<{count}{fmt_char}", raw))
        except Exception:
            return obj
    elif isinstance(obj, dict):
        return {k: decode_bdata(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decode_bdata(v) for v in obj]
    return obj


def clean_identifier(text: str) -> str:
    """Strip LaTeX math markup and special characters to create a clean identifier."""
    if not text:
        return "y"
    cleaned = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)
    cleaned = re.sub(r"[\$\\\{\}\(\)\[\]]", "", cleaned)
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "y"


def parse_html_to_figure(
    html_path: Union[str, Path],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract Plotly trace data and layout from an HTML file.

    Parameters
    ----------
    html_path : str or Path
        Path to the HTML file containing a Plotly figure.

    Returns
    -------
    tuple[list[dict], dict]
        (traces, layout) – the raw data/layout dictionaries
        with any base64-encoded arrays already decoded.

    Raises
    ------
    FileNotFoundError
        If *html_path* does not exist.
    ValueError
        If no ``Plotly.newPlot`` / ``Plotly.react`` call is found.
    """
    path = Path(html_path)
    if not path.is_file():
        raise FileNotFoundError(f"HTML file not found: {path}")

    content = path.read_text(encoding="utf-8")

    idx = content.rfind("Plotly.newPlot(")
    if idx == -1:
        idx = content.rfind("Plotly.react(")
    if idx == -1:
        raise ValueError(
            f"No Plotly plot found in '{path}' "
            "(missing Plotly.newPlot / Plotly.react)."
        )

    array_start = content.find("[", idx)
    if array_start == -1:
        raise ValueError(f"Malformed Plotly HTML in '{path}' (data array not found).")

    decoder = json.JSONDecoder()
    data, text_pos = decoder.raw_decode(content[array_start:])

    object_start = content.find("{", array_start + text_pos)
    if object_start == -1:
        raise ValueError(f"Malformed Plotly HTML in '{path}' (layout object not found).")

    layout, _ = decoder.raw_decode(content[object_start:])

    return decode_bdata(data), decode_bdata(layout)


def from_html(
    html_path: Union[str, Path],
    filename: Optional[str] = None,
    standalone: bool = False,
    tsv_threshold: int = 500,
) -> str:
    """
    Convert a Plotly HTML file to LaTeX/TikZ code.

    This is a convenience wrapper that parses the HTML file and
    delegates to :func:`plotikz.to_tikz`.

    Parameters
    ----------
    html_path : str or Path
        Path to the input Plotly HTML file.
    filename : str, optional
        If provided, save generated TikZ code to this filepath.
    standalone : bool, default False
        If True, produce a complete compilable LaTeX document.
    tsv_threshold : int, default 500
        Number of data points above which trace data is exported
        to external TSV files instead of inline tables.

    Returns
    -------
    str
        Generated LaTeX/TikZ code.
    """
    # Lazy import to avoid circular dependency
    from .plotly import to_tikz

    data, layout = parse_html_to_figure(html_path)
    fig_dict = {"data": data, "layout": layout}
    return to_tikz(
        fig_dict, filename=filename, standalone=standalone, tsv_threshold=tsv_threshold
    )
