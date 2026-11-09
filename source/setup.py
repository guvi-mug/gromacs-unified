"""Tag wheels carrying engines for their build OS without a Python ABI lock."""
from pathlib import Path
from setuptools import Distribution, setup
from wheel.bdist_wheel import bdist_wheel


def bundled():
    root = Path(__file__).parent / "src/gromacs_unified/runtime"
    return any((root / backend / "bin" / name).is_file()
               for backend in ("cpu", "cuda") for name in ("gmx", "gmx.exe"))


class EngineDistribution(Distribution):
    def has_ext_modules(self):
        return bundled()


class EngineWheel(bdist_wheel):
    def get_tag(self):
        python, abi, platform = super().get_tag()
        return ("py3", "none", platform) if bundled() else (python, abi, platform)


setup(distclass=EngineDistribution, cmdclass={"bdist_wheel": EngineWheel})
