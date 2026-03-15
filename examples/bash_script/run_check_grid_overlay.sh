#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root from this script location, so it works from any cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Editable parameters
UV_BIN="uv"
CLI_NAME="isoxml-inspect-grid-overlay"
SOURCE="${REPO_ROOT}/examples/output/big_xml_v3_type_1_auto"
SHP_PATH="${REPO_ROOT}/examples/input/big/shp/Rx.shp"
TASK_INDEX="0"
GRID_INDEX="0"
DDI="6"
SHOW_ZERO="true"
OUTPUT_PNG="${REPO_ROOT}/examples/output/big_xml_v3_type_1_auto/overlay_check.png"
OUTPUT_GEOJSON="${REPO_ROOT}/examples/output/big_xml_v3_type_1_auto/grid_cells.geojson"

CMD=(
  "${UV_BIN}" run "${CLI_NAME}"
  "${SOURCE}"
  --task-index "${TASK_INDEX}"
  --grid-index "${GRID_INDEX}"
  --ddi "${DDI}"
  --shp "${SHP_PATH}"
  --out "${OUTPUT_PNG}"
  --cells-out "${OUTPUT_GEOJSON}"
)

if [[ "${SHOW_ZERO}" == "true" ]]; then
  CMD+=(--show-zero)
fi

(
  cd "${REPO_ROOT}"
  "${CMD[@]}"
)
