"""
Python code generator from an existing TASKDATA.XML.

Uses xsdata's PycodeSerializer to emit runnable Python code that reconstructs
the task data object. Useful as a starting point when adapting a known-good
export from a real terminal.

See: https://xsdata.readthedocs.io/en/latest/data_binding/pycode_serializing/

Usage:
    python examples/pycode_generator.py
    # Output written to examples/output/generated_code.py
"""

from pathlib import Path

from xsdata.formats.dataclass.serializers import PycodeSerializer

from isoxml.io import read_from_path

BASE_DIR = Path(__file__).parent
INPUT_PATH = BASE_DIR.parent / "tests" / "resources" / "isoxml" / "v4" / "cnh_export" / "TASKDATA.XML"
OUTPUT_PATH = BASE_DIR / "output" / "generated_code.py"


def main() -> None:
    task_data, _refs = read_from_path(INPUT_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(PycodeSerializer().render(task_data, var_name="task_data"))
    print(f"Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
