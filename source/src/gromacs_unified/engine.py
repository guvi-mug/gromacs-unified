from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


class Gromacs:
    """Shared Windows/Linux interface; no shell or import-time probing."""

    def __init__(self, cpu=None, cuda=None, runtime_root=None):
        self.cpu = cpu or os.environ.get("GMX_CPU_EXECUTABLE")
        self.cuda = cuda or os.environ.get("GMX_CUDA_EXECUTABLE")
        self.runtime_root = runtime_root or os.environ.get("GMX_RUNTIME_ROOT")

    @staticmethod
    def _resolve(value):
        if not value:
            return None
        found = shutil.which(os.fspath(value))
        return str(Path(found).resolve()) if found else None

    @staticmethod
    def _environment(executable, overrides=None):
        """Scope dependent DLL/library lookup to the launched process."""
        env = os.environ.copy()
        if overrides:
            env.update({str(key): str(value) for key, value in overrides.items()})
        if executable:
            bindir = Path(executable).resolve().parent
            directories = [bindir, bindir.parent / "lib", bindir.parent / "lib64"]
            search = os.pathsep.join(str(path) for path in directories if path.is_dir())
            variable = "PATH" if os.name == "nt" else "LD_LIBRARY_PATH"
            previous = env.get(variable, "")
            env[variable] = search + (os.pathsep + previous if previous else "")
        return env

    @staticmethod
    def _probe(executable):
        if not executable:
            return None
        try:
            result = subprocess.run(
                [executable, "--version"], capture_output=True, text=True, timeout=10,
                env=Gromacs._environment(executable), encoding="utf-8", errors="replace"
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode:
            return None
        return result.stdout + result.stderr

    def _engines(self):
        roots = [Path(self.runtime_root)] if self.runtime_root else []
        roots.append(Path(__file__).resolve().parent / "runtime")
        name = "gmx.exe" if os.name == "nt" else "gmx"

        def discover(explicit, backend):
            if explicit:
                return self._resolve(explicit)
            for root in roots:
                found = self._resolve(root / backend / "bin" / name)
                if found:
                    return found
            return self._resolve("gmx")

        return discover(self.cpu, "cpu"), discover(self.cuda, "cuda")

    def doctor(self):
        """Report loadability and build features; mdrun detects usable devices."""
        cpu, cuda = self._engines()
        cpu_version = self._probe(cpu)
        cuda_version = self._probe(cuda)
        return {
            "runtime_root": str(self.runtime_root) if self.runtime_root else None,
            "cpu_executable": cpu,
            "cpu_loadable": cpu_version is not None,
            "cuda_executable": cuda,
            "cuda_loadable": cuda_version is not None,
            "cuda_compiled": self._has_cuda(cuda_version),
            "device_detection": "GROMACS mdrun at startup",
        }

    @staticmethod
    def _has_cuda(version):
        return bool(version and any(
            line.strip().lower().startswith("gpu support:") and "cuda" in line.lower()
            for line in version.splitlines()
        ))

    def command(self, tool, *args, backend="auto"):
        """Plan argv. auto lets mdrun select usable devices, respecting visibility."""
        if backend not in ("auto", "cpu", "cuda"):
            raise ValueError("backend must be auto, cpu, or cuda")
        if not tool or str(tool).startswith("-"):
            raise ValueError("a GROMACS tool name is required")
        args = [os.fspath(arg) if isinstance(arg, os.PathLike) else str(arg) for arg in args]
        if tool == "mdrun" and any(
            arg.split("=", 1)[0] in ("-nb", "-pme", "-pmefft", "-bonded", "-update")
            for arg in args
        ):
            raise ValueError("offload flags are managed by backend; use native gmx for custom offload")
        cpu, cuda = self._engines()
        cv = self._probe(cuda)
        if backend == "cuda":
            if not self._has_cuda(cv):
                raise RuntimeError("No loadable CUDA GROMACS engine; set GMX_CUDA_EXECUTABLE")
            executable = cuda
        elif backend == "auto" and self._has_cuda(cv):
            executable = cuda
        else:
            executable = cpu
            if self._probe(executable) is None:
                if backend == "cpu" and self.cpu:
                    raise RuntimeError("Configured CPU engine cannot be loaded: " + str(self.cpu))
                # A CUDA build can also run on CPU when its runtime loads.
                if cv is not None:
                    executable = cuda
                else:
                    raise RuntimeError("No loadable GROMACS engine; install GROMACS or set GMX_CPU_EXECUTABLE")
        flags = []
        if tool == "mdrun":
            if backend == "cpu":
                flags = ["-nb", "cpu", "-pme", "cpu", "-pmefft", "cpu",
                         "-bonded", "cpu", "-update", "cpu"]
            elif backend == "cuda":
                # Require GPU nonbonded work; retain automatic PME/update placement.
                flags = ["-nb", "gpu"]
        return [executable, str(tool), *args, *flags]

    def run(self, tool, *args, backend="auto", cwd=None, input=None,
            capture_output=False, check=True, timeout=None, env=None):
        """Run synchronously. CLI inherits streams; Python may capture or provide stdin.

        No retries after simulation startup: errors could leave output/checkpoints.
        Returns subprocess.CompletedProcess and preserves native exit status.
        """
        command = self.command(tool, *args, backend=backend)
        return subprocess.run(
            command, cwd=cwd, input=input,
            capture_output=capture_output, text=True, check=check, timeout=timeout,
            env=self._environment(command[0], env), encoding="utf-8", errors="replace"
        )

    def mdrun(self, *args, backend="auto", **kwargs):
        return self.run("mdrun", *args, backend=backend, **kwargs)
