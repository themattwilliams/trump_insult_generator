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

    def test_requirements_do_not_need_extra_tray_dependencies(self):
        requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()

        self.assertNotIn("pystray", requirements)
        self.assertNotIn("pillow", requirements)

    def test_windows_build_script_packages_one_file_exe(self):
        build_script = PROJECT_ROOT / "build_windows_exe.bat"
        build_requirements = PROJECT_ROOT / "requirements-build.txt"

        self.assertTrue(build_script.exists())
        self.assertTrue(build_requirements.exists())
        content = build_script.read_text(encoding="utf-8").lower()
        self.assertIn("pyinstaller", content)
        self.assertIn("--onefile", content)
        self.assertIn("--windowed", content)
        self.assertIn("--add-data", content)
        self.assertIn("trump.json", content)
        self.assertIn("trumpinsultgenerator", content)


if __name__ == "__main__":
    unittest.main()
