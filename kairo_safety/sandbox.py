"""Fail-closed launch boundary; this is not an OS sandbox by itself."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


class SandboxRefused(RuntimeError):
    pass


def manifest(root):
    root = Path(root).resolve()
    rows = {}
    for path in sorted((candidate for candidate in root.rglob("*") if candidate.is_file()), key=str):
        relative = path.relative_to(root).as_posix()
        rows[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return rows


def run(command, sandbox_root, allowed_executables, *, os_isolation_verified=False, timeout=30, max_output=20000):
    """Run only after an external OS isolation verifier has proven confinement.

    Python subprocess isolation, a temporary cwd, and environment scrubbing are
    defense-in-depth only. They are intentionally insufficient to authorize a
    real-program run, so the default is refusal.
    """
    root = Path(sandbox_root).resolve()
    if not root.is_dir(): raise SandboxRefused("sandbox root does not exist")
    if not command or Path(command[0]).name.lower() not in {name.lower() for name in allowed_executables}:
        raise SandboxRefused("executable is not allow-listed")
    if not os_isolation_verified:
        raise SandboxRefused("independent OS network/process isolation receipt is required")
    before = manifest(root); started = time.monotonic()
    environment = {"PATH": os.environ.get("PATH", ""), "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(command, cwd=root, env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=flags)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill(); stdout, stderr = process.communicate()
        raise SandboxRefused("sandbox task exceeded timeout")
    after = manifest(root)
    return {"returncode": process.returncode, "duration_seconds": time.monotonic() - started,
            "stdout": stdout[-max_output:], "stderr": stderr[-max_output:], "files_before": before,
            "files_after": after, "changed_files": sorted(set(before) | set(after)),
            "os_isolation_verified": True, "sandbox_root": str(root)}
