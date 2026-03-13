#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root from this script location, so it works from any cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Editable parameters
PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
SCRIPT_PATH="${REPO_ROOT}/examples/app_map_grid_type_2_from_shp.py"
SHP_PATH="${REPO_ROOT}/examples/input/small/shp/Rx.shp"
BOUNDARY_SHP="${REPO_ROOT}/examples/input/small/boundary/Boundary.shp"
XML_VERSION="3"
GRID_TYPE="1"
VALUE_FIELD="rate"
OUTPUT_DIR="${REPO_ROOT}/examples/output/small_xml_v3_auto"
OUTPUT_ZIP="${REPO_ROOT}/examples/output/small_xml_v3_auto.zip"
CELL_SIZE="3"
BOUNDARY_MASK="touch"
GRID_EXTENT="boundary"
"${PYTHON_BIN}" "${SCRIPT_PATH}" \
  "${SHP_PATH}" \
  --boundary-shp "${BOUNDARY_SHP}" \
  --xml-version "${XML_VERSION}" \
  --grid-type "${GRID_TYPE}" \
  --value-field "${VALUE_FIELD}" \
  --output-dir "${OUTPUT_DIR}" \
  --output-zip "${OUTPUT_ZIP}" \
  --value-unit kg/ha \
  --cell-size-m  "${CELL_SIZE}" \
  --boundary-mask "${BOUNDARY_MASK}" \
  --grid-extent "${GRID_EXTENT}"
