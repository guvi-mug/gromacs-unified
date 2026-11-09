#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 2 || $# -gt 3 ]]; then
    echo "Usage: $0 SOURCE_DIR INSTALL_DIR [cpu|both]" >&2
    exit 2
fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 "$script_dir/build_native.py" "$1" "$2" --backend "${3:-both}" --jobs "${BUILD_JOBS:-2}" --simd "${GMX_BUILD_SIMD:-SSE2}"
