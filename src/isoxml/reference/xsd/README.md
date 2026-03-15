These XSD files are bundled copies of the official ISOXML schemas published by the
[ISOBUS website](https://www.isobus.net/isobus/file/supportingDocuments).

They are stored in `src/isoxml/reference/xsd/` so the package can use them at runtime
via `importlib.resources`, without depending on an external checkout-time
`resources/` directory.

They are used in three two places:

1. Runtime XSD validation
   - `src/isoxml/xsd_validation.py` resolves the correct `ISO11783_TaskFile_V*-3.xsd`
     file from this directory and passes it to `xmlschema.validate(...)`.
   - This is used by public APIs and CLIs such as `validate_xsd(...)`,
     `isoxml-validate-taskdata`, `isoxml-shp-to-prescription`, and the
     prescription conversion pipeline.

2. Model generation reference
   - `src/isoxml/models/README.md` points to these files when regenerating the
     schema-derived dataclasses with `xsdata`.

In practice, the most important files are:
- `ISO11783_TaskFile_V3-3.xsd`
- `ISO11783_TaskFile_V4-3.xsd`

The other bundled schemas are kept alongside them because they are part of the
same official ISOXML schema set and are useful when inspecting exports or
regenerating models.
