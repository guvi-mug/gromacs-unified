import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location(
    'validation_utils', Path(__file__).resolve().parents[1] / 'scripts/validation_utils.py')
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)


class CheckpointTests(unittest.TestCase):
    def test_resume_runs_only_the_missing_steps(self):
        self.assertEqual(utils.remaining_steps(50000, 43920), 6080)
        self.assertEqual(utils.remaining_steps(2000, 750), 1250)

    def test_completed_checkpoint_needs_no_more_steps(self):
        self.assertEqual(utils.remaining_steps(50000, 50000), 0)
        self.assertEqual(utils.remaining_steps(50000, 50010), 0)
        with self.assertRaises(ValueError):
            utils.remaining_steps(50000, -1)

    def test_checkpoint_header_is_read_without_dumping_coordinates(self):
        process = mock.Mock()
        process.stdout = io.StringIO('header\nstep = 43920\ncoordinates follow\n')
        process.poll.return_value = None
        with mock.patch.object(utils.subprocess, 'Popen', return_value=process):
            self.assertEqual(utils.checkpoint_step(['gmx', 'dump'], {}), 43920)
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=10)
