"""Run a user-supplied program through Kairo's reset/step boundary.

The child speaks newline-delimited JSON on stdin/stdout:
  request: {"op":"describe"} -> {"alphabet":[...]}
  request: {"op":"reset"} -> {"ok":true}
  request: {"op":"step","action":"..."} -> {"output":"..."}

The path is executed directly, without a shell. Kairo does not inspect the
child's private state; only the declared alphabet and returned observations
cross the boundary.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


class PathProgramError(RuntimeError):
    pass


class PathProgram:
    def __init__(self, program_path, timeout=5.0):
        self.path = Path(program_path).expanduser().resolve()
        if not self.path.is_file():
            raise PathProgramError(f"program path is not a file: {self.path}")
        self.timeout = timeout
        command = [sys.executable, str(self.path)] if self.path.suffix == ".py" else [str(self.path)]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def request(self, payload):
        if self.process.poll() is not None:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise PathProgramError(f"program exited with {self.process.returncode}: {stderr[-500:]}")
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise PathProgramError("program returned no response")
        try:
            response = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PathProgramError("program returned invalid JSON") from exc
        if not isinstance(response, dict):
            raise PathProgramError("program response must be an object")
        return response

    def describe(self):
        response = self.request({"op": "describe"})
        alphabet = response.get("alphabet")
        if not isinstance(alphabet, list) or not alphabet or any(type(a) is not str for a in alphabet):
            raise PathProgramError("describe response must contain a non-empty string alphabet")
        return tuple(alphabet)

    def reset(self):
        response = self.request({"op": "reset"})
        if response.get("ok") is not True:
            raise PathProgramError("reset was not acknowledged")

    def step(self, action):
        response = self.request({"op": "step", "action": action})
        output = response.get("output")
        if type(output) is not str:
            raise PathProgramError("step response must contain a string output")
        return output

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=self.timeout)
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        if self.process.stdout and not self.process.stdout.closed:
            self.process.stdout.close()
        if self.process.stderr and not self.process.stderr.closed:
            self.process.stderr.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
