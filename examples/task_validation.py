"""
XSD validation example.

Shows how to validate generated ISOXML against the official ISO 11783-10 XSD
schema bundled with the package. Demonstrates both a valid and an invalid
task data document.

Usage:
    python examples/task_validation.py
"""

from importlib import resources

import xmlschema
from xmlschema import XMLSchemaValidationError

import isoxml.models.base.v4 as iso
from isoxml.io import to_xml


def get_xsd_path(version: str = "4", minor: str = "3"):
    xsd_name = f"ISO11783_TaskFile_V{version}-{minor}.xsd"
    return resources.files("isoxml.data.xsd").joinpath(xsd_name)


def main() -> None:
    xsd_ref = get_xsd_path()

    # --- valid document ---
    valid = iso.Iso11783TaskData(
        management_software_manufacturer="josephinum research",
        management_software_version="0.0.1",
        data_transfer_origin=iso.Iso11783TaskDataDataTransferOrigin.FMIS,
    )
    with resources.as_file(xsd_ref) as xsd_path:
        xmlschema.validate(to_xml(valid), xsd_path)
    print("Valid document: OK")

    # --- invalid document (missing required attributes) ---
    invalid = iso.Iso11783TaskData()
    try:
        with resources.as_file(xsd_ref) as xsd_path:
            xmlschema.validate(to_xml(invalid), xsd_path)
    except XMLSchemaValidationError as exc:
        print(f"Invalid document caught: {exc.reason}")


if __name__ == "__main__":
    main()
