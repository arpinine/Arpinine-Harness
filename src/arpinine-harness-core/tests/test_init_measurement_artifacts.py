from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "init_measurement_artifacts.py"


class InitMeasurementArtifactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify" / "evals" / "001-demo").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_scaffold_creates_templates_and_history_dir(self) -> None:
        result = subprocess.run(
            ["python3", str(SCRIPT), "--slug", "001-demo"],
            cwd=self.repo,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src" / "arpinine-harness-core" / "scripts")},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / ".specify" / "evals" / "001-demo" / "dataset-manifest.json").exists())
        self.assertTrue((self.repo / ".specify" / "evals" / "001-demo" / "baseline.json").exists())
        self.assertTrue((self.repo / ".specify" / "evals" / "001-demo" / "history").exists())


if __name__ == "__main__":
    unittest.main()
