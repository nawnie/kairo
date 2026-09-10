"""A real on-disk JSON deployment workflow, deliberately outside SQLite."""
from collections import Counter
import hashlib
import json
from pathlib import Path


class FileWorkflow:
    def __init__(self, root, case):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=False)
        self.path = self.root / "state.json"
        self.case = case
        self.bindings = case["bindings"]
        self.connection = None
        self.draft = None
        self.validated = False
        self.published = False
        self.meters = Counter({k: 0 for k in ("actions", "resets", "opens", "closes", "writes", "publishes", "reloads", "rollbacks", "validations")})
        self._write(case["baseline"])
        self.baseline_bytes = self.path.read_bytes()

    def _write(self, value):
        self.path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        self.meters["writes"] += 1

    def _read(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def close(self):
        if self.connection is not None:
            self.connection = None
            self.draft = None
            self.validated = False
            self.published = False
            self.meters["closes"] += 1

    def reset(self):
        self.close()
        self.path.write_bytes(self.baseline_bytes)
        self.meters["resets"] += 1

    def persisted(self):
        return self._read()

    def snapshot(self):
        return {"open": self.connection is not None, "draft": self.draft, "validated": self.validated,
                "published": self.published, "local": self.draft if self.draft is not None else self.persisted(),
                "persisted": self.persisted()}

    def disk_hash(self):
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def step(self, action):
        operation = self.bindings[action]
        self.meters["actions"] += 1
        if operation == "open":
            if self.connection is not None:
                return "already_open"
            self.connection = True
            self.meters["opens"] += 1
            return "session_opened"
        if operation == "close":
            if self.connection is None:
                return "already_closed"
            self.close()
            return "session_closed"
        if self.connection is None:
            return "session_required"
        if operation == "edit":
            self.draft = self.case["draft"]
            self.validated = False
            self.published = False
            return "draft_written"
        if operation == "validate":
            if self.draft is None:
                return "draft_required"
            self.validated = self.draft == self.case["draft"]
            self.meters["validations"] += 1
            return "validation_passed" if self.validated else "validation_failed"
        if operation == "publish":
            if self.draft is None or not self.validated:
                return "validated_draft_required"
            self._write(self.draft)
            self.published = True
            self.meters["publishes"] += 1
            return "published"
        if operation == "reload":
            self.draft = self.persisted()
            self.validated = False
            self.published = self.draft == self.case["draft"]
            self.meters["reloads"] += 1
            return "reloaded"
        if operation == "rollback":
            self.draft = None
            self.validated = False
            self.published = False
            self.meters["rollbacks"] += 1
            return "rolled_back"
        if operation == "inspect":
            local = self.draft if self.draft is not None else self.persisted()
            persisted = self.persisted()
            if local == self.case["draft"] and persisted == self.case["baseline"]:
                return "draft_verified"
            if local == persisted == self.case["draft"]:
                return "published_verified"
            if local == persisted == self.case["baseline"]:
                return "baseline_verified"
            return "unexpected_state"
        raise ValueError(operation)


def inspect_artifact(path, case):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"value": value, "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "matches": value == case["final_expected"], "valid_json": True}
