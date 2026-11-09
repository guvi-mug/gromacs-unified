import argparse
import json
import subprocess
import sys

from .engine import Gromacs


def main(argv=None):
    parser = argparse.ArgumentParser(description="Unified native GROMACS launcher")
    parser.add_argument("--backend", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--cpu-executable")
    parser.add_argument("--cuda-executable")
    parser.add_argument("--runtime-root", help="directory containing cpu/bin and cuda/bin")
    parser.add_argument("--dry-run", action="store_true", help="print argv as JSON")
    parser.add_argument("tool", help="GROMACS tool, or doctor")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    options = parser.parse_args(argv)
    engine = Gromacs(options.cpu_executable, options.cuda_executable, options.runtime_root)
    try:
        if options.tool == "doctor":
            print(json.dumps(engine.doctor(), indent=2))
            return 0
        args = options.args
        if args[:1] == ["--"]:
            args = args[1:]
        if options.dry_run:
            print(json.dumps(engine.command(options.tool, *args, backend=options.backend)))
            return 0
        result = engine.run(options.tool, *args, backend=options.backend, check=False)
        return result.returncode if result.returncode >= 0 else 128 - result.returncode
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(f"gmx-unified: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
