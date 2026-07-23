"""Extraction and formatting of Plotly layout annotations into TikZ nodes."""

from typing import Dict, Any, List
from ..utils import escape_tex, clean_val, format_color


def extract_annotations(layout_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse layout annotations into formatted TikZ node entries."""
    annotations_list = []
    raw_annotations = layout_data.get("annotations", [])
    if isinstance(raw_annotations, (list, tuple)):
        for ann in raw_annotations:
            if not isinstance(ann, dict):
                continue
            ax_val = clean_val(ann.get("x"))
            ay_val = clean_val(ann.get("y"))
            text_val = ann.get("text", "")
            if ax_val is not None and ay_val is not None and text_val:
                bgcolor = ann.get("bgcolor")
                bordercolor = ann.get("bordercolor")
                style_opts = ["font=\\small"]
                if bgcolor:
                    col_opt, _ = format_color(bgcolor)
                    if col_opt:
                        style_opts.append(col_opt.replace("color=", "fill="))
                else:
                    style_opts.append("fill=yellow!30")
                if bordercolor:
                    col_opt, _ = format_color(bordercolor)
                    if col_opt:
                        style_opts.append(col_opt.replace("color=", "draw="))
                else:
                    style_opts.append("draw=black!70")
                style_opts.append("rounded corners")
                style_opts.append("anchor=west")
                annotations_list.append({
                    "x": ax_val,
                    "y": ay_val,
                    "text": escape_tex(text_val),
                    "style": ", ".join(style_opts),
                })
    return annotations_list
