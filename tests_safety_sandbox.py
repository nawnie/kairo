import tempfile
import unittest
from pathlib import Path

from kairo_safety.sandbox import SandboxRefused, manifest, run


class SandboxTests(unittest.TestCase):
    def test_manifest_is_deterministic(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "input.txt"; path.write_text("bounded\n")
            first = manifest(root); second = manifest(root)
            self.assertEqual(first, second)
            self.assertIn("input.txt", first)

    def test_refuses_without_os_isolation_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(SandboxRefused):
                run(["python.exe", "-c", "print('no')"], root, {"python.exe"})

    def test_refuses_non_allowlisted_executable(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(SandboxRefused):
                run(["powershell.exe", "-NoProfile"], root, {"python.exe"}, os_isolation_verified=True)


if __name__ == "__main__": unittest.main()
