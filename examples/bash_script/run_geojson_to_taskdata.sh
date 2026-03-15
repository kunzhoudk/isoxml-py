#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root from this script location, so it works from any cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Editable parameters
UV_BIN="uv"
CLI_NAME="isoxml-vector-to-taskdata"
SOURCE_PATH="${REPO_ROOT}/examples/input/app_map_vector.geojson"
XML_VERSION="4"
GRID_TYPE="1"
VALUE_FIELD="dose"
CELL_SIZE="3"
BOUNDARY_MASK="touch"
GRID_EXTENT="boundary"
OUTPUT_BASENAME="app_map_vector_v${XML_VERSION}_type_${GRID_TYPE}_auto"
OUTPUT_DIR="${REPO_ROOT}/examples/output/${OUTPUT_BASENAME}"
OUTPUT_ZIP="${REPO_ROOT}/examples/output/${OUTPUT_BASENAME}.zip"

CMD=(
  "${UV_BIN}" run "${CLI_NAME}"
  "${SOURCE_PATH}"
  --xml-version "${XML_VERSION}"
  --grid-type "${GRID_TYPE}"
  --value-field "${VALUE_FIELD}"
  --output-dir "${OUTPUT_DIR}"
  --output-zip "${OUTPUT_ZIP}"
  --value-unit "kg/ha"
  --cell-size-m "${CELL_SIZE}"
  --boundary-mask "${BOUNDARY_MASK}"
  --grid-extent "${GRID_EXTENT}"
)

(
  cd "${REPO_ROOT}"
  "${CMD[@]}"
)
