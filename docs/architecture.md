# Architecture

This project now separates generated ISOXML models from the handwritten public API.

## Layout

- `src/isoxml/models/base/`: generated low-level ISOXML dataclasses for v2, v3, and v4.
- `src/isoxml/io/`: task data read/write helpers and external XML merge logic.
- `src/isoxml/geometry/`: Shapely conversion helpers.
- `src/isoxml/grids/`: NumPy <-> ISOXML grid binary encoding/decoding.
- `src/isoxml/prescriptions/`: high-level workflows for building application maps.
- `src/isoxml/cli/`: reusable CLI entry points.
- `src/isoxml/data/xsd/`: bundled runtime XSD schemas shipped inside the package.
- `src/isoxml/resources.py`: central resource lookup for bundled package data.

## Compatibility policy

Legacy modules under `isoxml.util`, `isoxml.converter`, and `isoxml.workflows` remain as compatibility shims.
New code should import from the public packages above instead of the legacy paths.

## Design intent

- Keep core algorithms and generated dataclasses stable.
- Move business workflows into explicit packages with narrower responsibilities.
- Make CLI code reusable outside `examples/`.
- Expose a clear public surface from `isoxml.__init__`.
