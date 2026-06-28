from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LauncherFileTests(unittest.TestCase):
    def test_batch_launcher_bootstraps_venv_and_runs_app(self):
        launcher = PROJECT_ROOT / "run_insult_generator.bat"

        self.assertTrue(launcher.exists())
        content = launcher.read_text(encoding="utf-8").lower()
        self.assertIn(".venv", content)
        self.assertIn("scripts\\python.exe", content)
        self.assertIn("-m venv", content)
        self.assertIn("-r", content)
        self.assertIn("requirements.txt", content)
        self.assertIn("insults.py", content)
        self.assertIn("requirements.sha256", content)
        self.assertIn("certutil -hashfile", content)
        self.assertIn("dependencies are current", content)
        self.assertIn("dependencies_changed", content)

    def test_gitignore_excludes_project_venv(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn(".venv/", gitignore)


if __name__ == "__main__":
    unittest.main()
