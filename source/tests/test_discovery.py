import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gromacs_unified import Gromacs


class DiscoveryTests(unittest.TestCase):
    def test_runtime_layout_discovery_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='gmx path ') as directory:
            root = Path(directory)
            expected = []
            for backend in ('cpu', 'cuda'):
                executable = root / backend / 'bin' / ('gmx.exe' if os.name == 'nt' else 'gmx')
                executable.parent.mkdir(parents=True)
                executable.write_text('fixture')
                executable.chmod(0o755)
                expected.append(str(executable.resolve()))
            engine = Gromacs(runtime_root=root)
            engine.cpu = engine.cuda = None
            self.assertEqual(engine._engines(), tuple(expected))

    def test_missing_explicit_cpu_is_not_replaced_by_path(self):
        engine = Gromacs(cpu='/does/not/exist/gmx')
        self.assertIsNone(engine._engines()[0])
        with patch.object(engine, '_probe', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'Configured CPU'):
                engine.command('mdrun', backend='cpu')

    def test_runtime_root_environment(self):
        with patch.dict(os.environ, {'GMX_RUNTIME_ROOT': 'runtime directory'}):
            self.assertEqual(Gromacs().runtime_root, 'runtime directory')

    def test_environment_is_scoped_and_keeps_visibility(self):
        before = dict(os.environ)
        result = Gromacs._environment(__file__, {'CUDA_VISIBLE_DEVICES': '', 'TEST_CHILD': '1'})
        self.assertEqual(result['CUDA_VISIBLE_DEVICES'], '')
        self.assertEqual(result['TEST_CHILD'], '1')
        self.assertEqual(dict(os.environ), before)
        self.assertIn(str(Path(__file__).resolve().parent),
                      result['PATH' if os.name == 'nt' else 'LD_LIBRARY_PATH'])

    def test_numeric_native_options(self):
        engine = Gromacs()
        with patch.object(engine, '_engines', return_value=('cpu', None)), \
                patch.object(engine, '_probe', side_effect=lambda path: 'GPU support: disabled' if path else None):
            self.assertIn('20', engine.command('mdrun', '-nsteps', 20))
