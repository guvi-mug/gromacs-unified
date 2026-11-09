import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import patch

from gromacs_unified import Gromacs
from gromacs_unified.cli import main


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = Gromacs()
        self.paths = patch.object(Gromacs, "_engines", return_value=("cpu", "cuda"))
        self.paths.start()
        self.addCleanup(self.paths.stop)
        self.versions = {"cpu": "GPU support: disabled", "cuda": "GPU support: CUDA"}
        probe = patch.object(Gromacs, "_probe", side_effect=self.versions.get)
        probe.start()
        self.addCleanup(probe.stop)

    def test_auto_delegates_hardware_detection(self):
        self.assertEqual(self.engine.command("mdrun", "-s", "run.tpr"),
                         ["cuda", "mdrun", "-s", "run.tpr"])

    def test_cpu_forces_all_offload_to_cpu(self):
        command = self.engine.command("mdrun", backend="cpu")
        self.assertEqual(command[0], "cpu")
        for flag in ("-nb", "-pme", "-pmefft", "-bonded", "-update"):
            self.assertEqual(command[command.index(flag) + 1], "cpu")

    def test_cuda_requires_gpu_nonbonded(self):
        self.assertEqual(self.engine.command("mdrun", backend="cuda"),
                         ["cuda", "mdrun", "-nb", "gpu"])

    def test_unloadable_cuda_falls_back_before_start(self):
        self.versions["cuda"] = None
        self.assertEqual(self.engine.command("mdrun")[0], "cpu")
        with self.assertRaises(RuntimeError):
            self.engine.command("mdrun", backend="cuda")

    def test_non_cuda_build_rejected(self):
        self.versions["cuda"] = "GPU support: SYCL"
        with self.assertRaises(RuntimeError):
            self.engine.command("mdrun", backend="cuda")

    def test_missing_engines(self):
        self.versions.clear()
        with self.assertRaises(RuntimeError):
            self.engine.command("mdrun")

    def test_single_cuda_engine_can_run_cpu(self):
        self.versions["cpu"] = None
        self.assertEqual(self.engine.command("mdrun", backend="cpu")[0], "cuda")

    def test_other_tools_have_no_mdrun_flags(self):
        self.assertEqual(self.engine.command("grompp", "-f", "test.mdp", backend="cpu"),
                         ["cpu", "grompp", "-f", "test.mdp"])

    def test_conflicting_flags_and_invalid_backend(self):
        for args in (("-nb", "gpu"), ("-update=cpu",)):
            with self.assertRaises(ValueError):
                self.engine.command("mdrun", *args)
        with self.assertRaises(ValueError):
            self.engine.command("mdrun", backend="typo")

    def test_subprocess_options_and_no_retry(self):
        with patch("gromacs_unified.engine.subprocess.run") as run:
            run.side_effect = subprocess.CalledProcessError(1, ["cuda", "mdrun"])
            with self.assertRaises(subprocess.CalledProcessError):
                self.engine.mdrun("-s", "space in path.tpr", cwd="work", capture_output=True)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][3], "space in path.tpr")
            self.assertEqual(run.call_args.kwargs["cwd"], "work")

    def test_cli_passthrough_and_exit_status(self):
        with patch.object(Gromacs, "run", return_value=subprocess.CompletedProcess([], 7)) as run:
            self.assertEqual(main(["--backend", "cpu", "mdrun", "-s", "run.tpr"]), 7)
            run.assert_called_once_with("mdrun", "-s", "run.tpr", backend="cpu", check=False)

    def test_doctor_does_not_claim_device_detection(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["doctor"]), 0)
        self.assertTrue(json.loads(out.getvalue())["cuda_compiled"])


class ProbeTests(unittest.TestCase):
    def test_timeout_or_dynamic_linker_failure(self):
        for failure in (OSError("missing runtime"), subprocess.TimeoutExpired("gmx", 10)):
            with patch("gromacs_unified.engine.subprocess.run", side_effect=failure):
                self.assertIsNone(Gromacs._probe("gmx"))


if __name__ == "__main__":
    unittest.main()
