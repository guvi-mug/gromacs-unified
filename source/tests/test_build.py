import argparse
import importlib.util
import json
from pathlib import Path
import platform
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class BuildTests(unittest.TestCase):
    def test_both_backend_command_plans(self):
        args = argparse.Namespace(simd='SSE2', fftw_prefix='fftw', generator=None,
                                  fft='fftw3', cmake_arg=[], jobs=2, skip_checks=False)
        builder = module('build_native')
        for backend, gpu in [('cpu', 'OFF'), ('cuda', 'CUDA')]:
            commands = builder.commands(Path('source'), Path('runtime'), Path('work'), backend, args)
            self.assertIn('-DGMX_GPU=' + gpu, commands[0])
            self.assertIn('-DGMX_BUILD_OWN_FFTW=OFF', commands[0])
            self.assertIn('check', commands[2])
            self.assertIn('--install', commands[3])

    def test_bundle_staging_and_validation(self):
        stage = module('stage_runtime').stage
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root / 'source', root / 'package/runtime'
            binary = source / 'cpu/bin' / ('gmx.exe' if platform.system() == 'Windows' else 'gmx')
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'native-fixture')
            manifest = source / 'cpu/build-info.json'
            info = {'backend': 'cpu', 'system': platform.system(), 'machine': platform.machine(),
                    'checks_passed': False}
            manifest.write_text(json.dumps(info))
            with self.assertRaisesRegex(ValueError, 'checks were skipped'):
                stage(source, target)
            self.assertFalse(target.exists())
            stage(source, target, allow_unchecked=True)
            self.assertEqual((target / 'cpu/bin' / binary.name).read_bytes(), b'native-fixture')
            with self.assertRaises(FileExistsError):
                stage(source, target, allow_unchecked=True)

    def test_staging_rejects_mismatched_platform(self):
        stage = module('stage_runtime').stage
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'cpu/bin').mkdir(parents=True)
            binary = root / 'cpu/bin' / ('gmx.exe' if platform.system() == 'Windows' else 'gmx')
            binary.touch()
            (root / 'cpu/build-info.json').write_text(json.dumps({
                'system': 'wrong-system', 'machine': platform.machine(), 'checks_passed': True}))
            with self.assertRaisesRegex(ValueError, 'platform'):
                stage(root, root.parent / (root.name + '-package'))

    def test_pinned_source_hashes_are_sha256(self):
        for _, _, checksum in module('fetch_sources').SOURCES.values():
            self.assertEqual(len(checksum), 64)
            int(checksum, 16)

    def test_corrupt_cached_release_is_rejected_before_extraction(self):
        fetcher = module('fetch_sources')
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            archive = destination / 'gromacs-2026.4.tar.gz'
            archive.write_bytes(b'tampered release archive')
            with mock.patch.object(fetcher.urllib.request, 'urlopen') as download:
                with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
                    fetcher.fetch('gromacs', destination)
                download.assert_not_called()
            self.assertFalse((destination / 'gromacs-2026.4').exists())
