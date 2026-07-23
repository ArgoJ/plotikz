"""Base abstract class for trace handlers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Set, Optional, List, Tuple
from ..utils import escape_tex, clean_val, format_coord_val


class TraceHandler(ABC):
    """Base class for Plotly trace conversion handlers."""

    def __init__(self):
        self.packages: Set[str] = set()
        self.libraries: Set[str] = set()

    @abstractmethod
    def can_handle(self, trace_type: str) -> bool:
        """Check if this handler supports trace_type."""
        pass

    @abstractmethod
    def process(
        self,
        trace: Dict[str, Any],
        trace_index: int,
        tsv_threshold: int = 500,
        tsv_prefix: Optional[str] = None,
        base_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process trace and return trace metadata dictionary."""
        pass

    # -------------------------------------------------------------------------
    # Common Shared Utility Methods (DRY)
    # -------------------------------------------------------------------------

    @staticmethod
    def _to_list(val: Any) -> List[Any]:
        """Safely convert numpy arrays, pandas series, or iterables into a standard Python list."""
        if hasattr(val, "tolist") and callable(getattr(val, "tolist", None)):
            return val.tolist()
        if hasattr(val, "values") and not isinstance(val, dict):
            vals = getattr(val, "values")
            return vals if not callable(vals) else list(vals)
        if isinstance(val, (list, tuple)):
            return list(val)
        return []

    def _extract_xy_coords(self, trace: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Extract cleaned and formatted (x, y) coordinate pairs from trace dict."""
        raw_x = self._to_list(trace.get("x", []))
        raw_y = self._to_list(trace.get("y", []))

        coords = []
        for xi, yi in zip(raw_x, raw_y):
            cx = clean_val(xi)
            cy = clean_val(yi)
            if cx is not None and cy is not None:
                coords.append((format_coord_val(cx), format_coord_val(cy)))
        return coords

    @staticmethod
    def _extract_legend_entry(trace: Dict[str, Any], default_showlegend: bool = True) -> Optional[str]:
        """Extract LaTeX-escaped legend entry if legend display is enabled for trace."""
        name = trace.get("name")
        showlegend = trace.get("showlegend", default_showlegend)
        if name and showlegend is not False:
            return escape_tex(name)
        return None

    @staticmethod
    def _extract_line_dash(line_cfg: Dict[str, Any]) -> Optional[str]:
        """Map Plotly dash style string to PGFPlots style string."""
        line_dash = line_cfg.get("dash")
        dash_map = {
            "dash": "dashed",
            "dot": "dotted",
            "dashdot": "dashdotted",
            "solid": "solid",
            "longdash": "densely dashed",
            "longdashdot": "densely dashdotted",
        }
        return dash_map.get(line_dash)

    def _format_data_output(
        self,
        coords: List[Tuple[str, ...]],
        trace_index: int,
        tsv_threshold: int,
        tsv_prefix: Optional[str],
        default_data_type: str = "table_macro",
        cols: Tuple[str, ...] = ("x", "y"),
    ) -> Dict[str, str]:
        """Format coordinates into TSV output, table_macro content, or inline coordinates."""
        n_points = len(coords)
        prefix = tsv_prefix or "data"

        if n_points > tsv_threshold:
            tsv_filename = f"{prefix}_trace_{trace_index}.tsv"
            sep = "\t"
            header = sep.join(cols)
            tsv_lines = [header] + [sep.join(c) for c in coords]
            return {
                "data_type": "tsv",
                "tsv_filename": tsv_filename,
                "tsv_content": "\n".join(tsv_lines),
                "table_content": "",
                "inline_coords": "",
            }

        header = " ".join(cols)
        lines = [header] + [" ".join(c) for c in coords]
        table_content = "\n".join(lines)

        if len(cols) == 3:
            inline_coords = " ".join([f"({c[0]}, {c[1]}) [{c[2]}]" for c in coords])
        else:
            inline_coords = " ".join([f"({c[0]}, {c[1]})" for c in coords])

        return {
            "data_type": default_data_type,
            "tsv_filename": "",
            "tsv_content": "",
            "table_content": table_content,
            "inline_coords": inline_coords,
        }
