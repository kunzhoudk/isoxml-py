# Examples

Install the optional example dependencies first:

```bash
pip install .[dev]
```

## Recommended entry points

- `maps/app_map_grid_type_2_from_shp.py`: build ISOXML application maps from polygon shapefiles.
- `maps/check_grid_overlay.py`: inspect grid alignment against partfield boundaries.
- `maps/read_grid_type_2_bin.py`: decode `GRD*.bin` payloads back to NumPy arrays.
- `maps/validate_grid_bin.py`: validate binary grid content and compare it with source shapefile values.

## Additional examples

- `maps/app_map_grid_type_1.py`: minimal grid type 1 export example.
- `maps/app_map_grid_type_2.py`: minimal grid type 2 export example.
- `maps/app_map_vector.py`: vector-based application map example.
- `guidance/guidance_pattern.py`: guidance pattern export example.
- `geometry/partfield_export.py`: partfield export example.
- `tooling/inspect_shapefile.py`: inspect shapefile attributes and CRS.
- `tooling/pycode_generator.py`: render Python code from an existing `TASKDATA.XML`.
- `tooling/task_validation.py`: validate generated task data against the packaged XSD.

## Notebooks

- `guidance/guidance_pattern_viewer.ipynb`
- `geometry/partfield_viewer.ipynb`

These notebooks are exploratory and may lag behind the Python script APIs.

## Inputs and outputs

- `examples/input/` contains sample datasets used by tests and examples.
- `examples/output/` is for generated files and is intentionally gitignored.
