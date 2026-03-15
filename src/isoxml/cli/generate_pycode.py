"""CLI for generating Python code from existing ISOXML TaskData."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from xsdata.formats.dataclass.serializers import PycodeSerializer

from isoxml.cli._common import load_taskdata


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    default_input = (
        Path(__file__).resolve().parents[3]
        / "tests"
        / "resources"
        / "isoxml"
        / "v4"
        / "cnh_export"
        / "TASKDATA.XML"
    )
    default_output = (
        Path(__file__).resolve().parents[3]
        / "examples"
        / "output"
        / "generated_code.py"
    )
    parser = argparse.ArgumentParser(
        description="Generate Python code from existing ISOXML TaskData."
    )
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=default_input,
        help="TASKDATA directory, XML file, or ZIP archive.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Output Python file path.",
    )
    parser.add_argument(
        "--var-name",
        type=str,
        default="task_data",
        help="Variable name used in generated code.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    task_data = load_taskdata(args.source, read_bin_files=False)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file_handle:
        file_handle.write(PycodeSerializer().render(task_data, var_name=args.var_name))
    print(f"Generated: {args.output}")


if __name__ == "__main__":
    main()
