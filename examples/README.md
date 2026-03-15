# examples

This directory is now mostly for:
- demonstration scripts
- notebooks
- sample input/output data
- themed example modules and formal CLI-adjacent data

Before you start, install the development dependencies:

```bash
pip install .[dev]
```

If you want stable command-line entry points, prefer the CLI commands instead of calling files in `examples/` directly:

```bash
uv run isoxml-shp-to-taskdata --help
uv run isoxml-convert-taskdata --help
uv run isoxml-inspect-grid-overlay --help
uv run isoxml-inspect-shapefile --help
uv run isoxml-validate-grid-bin --help
uv run isoxml-inspect-grid --help
uv run isoxml-validate-taskdata --help
uv run isoxml-generate-pycode --help
```

Current rough split:
- `application_maps/`: vector and grid application map demos
- `guidance/`: guidance pattern demos
- `partfields/`: partfield export demos
- `partfield_viewer.ipynb`: interactive partfield viewer
- `grid_overlay_viewer.ipynb`: interactive grid/partfield overlay viewer
- `input/`: source sample data
- `expected/`: fixed example outputs kept in git for docs and notebooks
- `output/`: local runtime output from scripts and CLI commands
