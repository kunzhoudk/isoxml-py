#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EXAMPLES_DIR="${REPO_ROOT}/examples"

SHP_PATH="${EXAMPLES_DIR}/input/small/shp/Rx.shp"
BOUNDARY_SHP="${EXAMPLES_DIR}/input/small/boundary/Boundary.shp"
OUTPUT_DIR="${EXAMPLES_DIR}/output/app_map_grid_type_2_from_shp"
OUTPUT_ZIP="${EXAMPLES_DIR}/output/app_map_grid_type_2_from_shp.zip"

if [ "$#" -gt 0 ] && [[ "${1}" != --* ]]; then
    SHP_PATH="${1}"
    shift
fi

if [ "$#" -gt 0 ] && [[ "${1}" != --* ]]; then
    BOUNDARY_SHP="${1}"
    shift
fi

if [ "$#" -gt 0 ] && [[ "${1}" != --* ]]; then
    OUTPUT_DIR="${1}"
    shift
fi

if [ "$#" -gt 0 ] && [[ "${1}" != --* ]]; then
    OUTPUT_ZIP="${1}"
    shift
fi

EXTRA_ARGS=("$@")

cd "${REPO_ROOT}"

uv run isoxml-grid-from-shp \
    "${SHP_PATH}" \
    --boundary-shp "${BOUNDARY_SHP}" \
    --grid-type 2 \
    --xml-version 3 \
    --value-unit auto \
    --cell-size-m 3.0 \
    --boundary-mask touch \
    --grid-extent boundary \
    --output-dir "${OUTPUT_DIR}" \
    --output-zip "${OUTPUT_ZIP}" \
    "${EXTRA_ARGS[@]:+${EXTRA_ARGS[@]}}"
