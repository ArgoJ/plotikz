"""CLI entry point for plotikz.

Usage:
    python -m plotikz file1.html file2.html                     # convert HTML → .tex
    python -m plotikz file.html -o output.tex                   # explicit output path
    python -m plotikz --standalone file.html                    # full LaTeX document
    python -m plotikz file.html -k colorbar_ticks=6             # key=val kwargs
"""

import argparse
import sys
from pathlib import Path

from .plotly.html_parser import from_html


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="plotikz",
        description="Convert Plotly HTML files to TikZ/PGFPlots (.tex) figures.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Path(s) to Plotly HTML file(s).",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output .tex file path (only for a single input file).",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Generate a complete, compilable LaTeX document.",
    )
    parser.add_argument(
        "--tsv-threshold",
        type=int,
        default=500,
        help="Data-point threshold for exporting to external TSV files (default: 500).",
    )
    parser.add_argument(
        "-k", "--kwarg",
        action="append",
        metavar="KEY=VAL",
        help="Custom plot-specific keyword arguments (e.g. -k colorbar_ticks=6).",
    )

    args = parser.parse_args()

    if args.output and len(args.files) > 1:
        print(
            "Error: --output can only be used with a single input file.",
            file=sys.stderr,
        )
        sys.exit(1)

    extra_kwargs = {}

    if args.kwarg:
        for kv in args.kwarg:
            if "=" in kv:
                key, val = kv.split("=", 1)
                key = key.strip()
                val = val.strip()
                if val.isdigit():
                    val = int(val)
                else:
                    try:
                        val = float(val)
                    except ValueError:
                        if val.lower() == "true":
                            val = True
                        elif val.lower() == "false":
                            val = False
                extra_kwargs[key] = val

    for html_path in args.files:
        if not html_path.is_file():
            print(f"Error: file not found: {html_path}", file=sys.stderr)
            sys.exit(1)

        out_path = str(args.output) if args.output else str(html_path.with_suffix(".tex"))
        try:
            print(f"⏳ Converting {html_path} ...")
            from_html(
                html_path,
                filename=out_path,
                standalone=args.standalone,
                tsv_threshold=args.tsv_threshold,
                **extra_kwargs,
            )
            print(f"✅ {out_path}")
        except Exception as exc:
            print(f"❌ {html_path}: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
