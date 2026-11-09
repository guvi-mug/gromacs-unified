# Source this file from the project directory: source ./activate-gromacs-wsl.sh
_gromacs_project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$_gromacs_project_dir/.venv-wsl/bin/activate"
export GMX_RUNTIME_ROOT="$_gromacs_project_dir/.native/linux/runtime"
unset _gromacs_project_dir
