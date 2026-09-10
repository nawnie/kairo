"""Deterministic, evidence-first source summary for a supplied program path."""
from __future__ import annotations

import ast
from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib


@dataclass(frozen=True)
class SourceEvidence:
    path: str
    line: int
    text: str

    def as_dict(self):
        return {"path": self.path, "line": self.line, "text": self.text}


def _files(root: Path):
    if root.is_file():
        return [root]
    excluded = {".git", "__pycache__", ".pytest_cache", "results", "datasets", "delivery", "verification", "sources", "archive", "archives", "kairo_discovery_lab_r5_endogenous_explanations"}
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part.lower() in excluded for part in path.parts):
            continue
        if any(token in path.name.lower() for token in ("private", "truth", "receipt", "secret", "credential")):
            continue
        files.append(path)
    return sorted(files)


def _python_summary(path: Path):
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return [], None
    items = []
    imports = []
    functions = []
    classes = []
    behaviors = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "relative import")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"open", "connect", "urlopen", "Popen", "run", "system", "loads", "dumps"}:
            behaviors.append(node.func.id)
    if imports:
        items.append(SourceEvidence(str(path), 1, "imports: " + ", ".join(sorted(set(imports)))))
    if classes:
        items.append(SourceEvidence(str(path), 1, "classes: " + ", ".join(sorted(set(classes)))))
    if functions:
        items.append(SourceEvidence(str(path), 1, "functions: " + ", ".join(sorted(set(functions)))))
    if behaviors:
        items.append(SourceEvidence(str(path), 1, "operations: " + ", ".join(sorted(set(behaviors)))))
    if any(isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__" for node in tree.body):
        items.append(SourceEvidence(str(path), 1, "has __main__ entry-point guard"))
    return items, ast.get_docstring(tree, clean=True)


def _text_source_summary(path: Path):
    source = path.read_text(encoding="utf-8", errors="replace")
    items = []
    imports = sorted(set(re.findall(r"(?:import|require\s*\()\s*[\"']?([A-Za-z0-9_./@-]+)", source)))
    functions = sorted(set(re.findall(r"(?:function\s+|(?:fn|func|void|int|string|public|private)\s+)([A-Za-z_]\w*)\s*\(", source)))
    if imports:
        items.append(SourceEvidence(str(path), 1, "imports: " + ", ".join(imports[:30])))
    if functions:
        items.append(SourceEvidence(str(path), 1, "functions: " + ", ".join(functions[:30])))
    return items


def summarize_path(program_path):
    root = Path(program_path).expanduser().resolve()
    if not root.exists():
        return {"status": "error", "reason": "program_path_not_found", "answer": None, "evidence": []}
    files = _files(root)
    evidence = []
    descriptions = []
    docs = []
    entrypoints = []
    metadata = []
    operations = set()
    for path in files:
        relative = path.name if root.is_file() else str(path.relative_to(root))
        if path.suffix.lower() in {".md", ".txt", ".rst"} and path.name.lower() in {"readme.md", "readme.txt", "readme.rst", "description.md"}:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            useful = [(index, line.strip()) for index, line in enumerate(lines, 1) if line.strip()][:8]
            for line, text in useful:
                docs.append(text)
                evidence.append(SourceEvidence(str(path), line, text))
        elif path.suffix.lower() == ".py":
            items, docstring = _python_summary(path)
            evidence.extend(items)
            for item in items:
                if item.text.startswith("operations:"):
                    operations.update(item.text.split(":", 1)[1].split(", "))
            if docstring:
                descriptions.append(docstring.splitlines()[0])
            if path.name in {"main.py", "__main__.py", "cli.py"}:
                entrypoints.append(str(path))
        elif path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cs", ".cpp", ".c", ".h"}:
            items = _text_source_summary(path)
            evidence.extend(items)
        elif path.name == "pyproject.toml":
            try:
                config = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
                project = config.get("project", {})
                if project.get("name"):
                    metadata.append(f"Python package: {project['name']}")
                if project.get("description"):
                    metadata.append(str(project["description"]))
                if project.get("scripts"):
                    metadata.append("declares command-line scripts: " + ", ".join(sorted(project["scripts"])))
            except (tomllib.TOMLDecodeError, OSError):
                pass
        elif path.name == "package.json":
            try:
                package = json.loads(path.read_text(encoding="utf-8", errors="replace"))
                if package.get("name"):
                    metadata.append(f"Node package: {package['name']}")
                if package.get("description"):
                    metadata.append(str(package["description"]))
                if package.get("scripts"):
                    metadata.append("declares scripts: " + ", ".join(sorted(package["scripts"])))
            except (json.JSONDecodeError, OSError):
                pass
    if not files:
        return {"status": "abstain", "reason": "no_readable_files", "answer": None, "evidence": []}
    parts = []
    if docs:
        parts.append("Project documentation says: " + " ".join(docs[:3]))
    if descriptions:
        parts.append("Python module descriptions: " + " ".join(descriptions[:5]))
    if metadata:
        parts.append("Package metadata: " + " ".join(metadata[:4]))
    if entrypoints:
        parts.append("Likely entry-point files include: " + ", ".join(entrypoints[:8]))
    if operations:
        parts.append("Source-visible operations include: " + ", ".join(sorted(operations)) + ".")
    python_count = sum(path.suffix.lower() == ".py" for path in files)
    if python_count:
        parts.append(f"The supplied location contains {python_count} Python source file(s) summarized by their imports, classes, and functions.")
    if not parts:
        parts.append(f"The supplied location contains {len(files)} readable file(s), but no supported description or Python structure was found.")
    return {"status": "answered", "answer": " ".join(parts),
            "scope": "source summary only; runtime behavior requires execution evidence",
            "evidence": [item.as_dict() for item in evidence[:40]],
            "files_considered": len(files)}


def summarize_function(program_path, function_name):
    root = Path(program_path).expanduser().resolve()
    if not root.exists():
        return {"status": "error", "reason": "program_path_not_found", "answer": None, "evidence": []}
    matches = []
    for path in _files(root):
        if path.suffix.lower() != ".py":
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                doc = ast.get_docstring(node, clean=True)
                calls = sorted({call.func.id for call in ast.walk(node)
                                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)})
                returns = [ast.get_source_segment(source, item.value) for item in ast.walk(node)
                           if isinstance(item, ast.Return) and item.value is not None]
                evidence = [SourceEvidence(str(path), node.lineno, f"def {node.name}(...)")]
                if doc:
                    evidence.append(SourceEvidence(str(path), node.lineno, doc.splitlines()[0]))
                answer = f"{function_name} is defined in {path.name}."
                if doc:
                    answer += f" Documentation: {doc.splitlines()[0]}"
                if calls:
                    answer += f" It directly calls: {', '.join(calls)}."
                if returns:
                    answer += f" It has return expression(s): {', '.join(returns[:5])}."
                else:
                    answer += " No explicit return expression was found in the source."
                matches.append({"status": "answered", "answer": answer,
                                "scope": "static source summary only; runtime behavior requires execution evidence",
                                "evidence": [item.as_dict() for item in evidence]})
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return {"status": "abstain", "reason": "function_name_is_ambiguous", "answer": None,
                "evidence": [item for match in matches for item in match["evidence"]]}
    return {"status": "abstain", "reason": "function_not_found", "answer": None, "evidence": []}


def find_symbol(program_path, symbol):
    root = Path(program_path).expanduser().resolve()
    matches = []
    for path in _files(root):
        if path.suffix.lower() != ".py":
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol:
                kind = "function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class"
                matches.append(SourceEvidence(str(path), node.lineno, f"{kind} {symbol}"))
    if len(matches) == 1:
        item = matches[0]
        return {"status": "answered", "answer": f"{symbol} is defined at {item.path}:{item.line}.",
                "evidence": [item.as_dict()]}
    if len(matches) > 1:
        return {"status": "abstain", "reason": "symbol_name_is_ambiguous", "answer": None,
                "evidence": [item.as_dict() for item in matches]}
    return {"status": "abstain", "reason": "symbol_not_found", "answer": None, "evidence": []}


def find_text(program_path, term):
    root = Path(program_path).expanduser().resolve()
    if not root.exists():
        return {"status": "error", "reason": "program_path_not_found", "answer": None, "evidence": []}
    matches = []
    needle = term.lower()
    for path in _files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            if needle in line.lower():
                matches.append(SourceEvidence(str(path), number, line.strip()))
    if not matches:
        return {"status": "abstain", "reason": "text_not_found", "answer": None, "evidence": []}
    return {"status": "answered", "answer": f"Found {len(matches)} matching line(s) for {term!r}.",
            "evidence": [item.as_dict() for item in matches[:40]], "matches": len(matches)}


def capability(program_path, name):
    groups = {
        "network": {"requests", "urllib", "http", "socket", "urlopen", "websocket"},
        "file": {"open", "pathlib", "shutil", "os", "glob"},
        "database": {"sqlite", "sqlalchemy", "psycopg", "mysql", "connect"},
        "process": {"subprocess", "popen", "system", "os.system"},
    }
    terms = groups.get(name.lower())
    if not terms:
        return {"status": "abstain", "reason": "unsupported_capability", "answer": None, "evidence": []}
    root = Path(program_path).expanduser().resolve()
    matches = []
    for path in _files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            lowered = line.lower()
            if any(term in lowered for term in terms):
                matches.append(SourceEvidence(str(path), number, line.strip()))
    answer = "yes" if matches else "no"
    return {"status": "answered", "answer": answer,
            "scope": "static source indicators only; does not prove runtime activity",
            "evidence": [item.as_dict() for item in matches[:40]], "matches": len(matches)}


def dependencies(program_path):
    root = Path(program_path).expanduser().resolve()
    found = []
    evidence = []
    for path in _files(root):
        if path.suffix.lower() == ".py":
            items, _ = _python_summary(path)
        elif path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cs", ".cpp", ".c", ".h"}:
            items = _text_source_summary(path)
        else:
            items = []
        for item in items:
            if item.text.startswith("imports:"):
                found.extend(item.text.split(":", 1)[1].split(", "))
                evidence.append(item)
    unique = sorted(set(item.strip() for item in found if item.strip()))
    return {"status": "answered", "answer": ", ".join(unique) if unique else "No imports were identified.",
            "evidence": [item.as_dict() for item in evidence[:40]], "dependencies": unique}


def entrypoints(program_path):
    root = Path(program_path).expanduser().resolve()
    found = []
    evidence = []
    for path in _files(root):
        if path.name in {"main.py", "__main__.py", "cli.py", "index.js", "index.ts", "main.go", "Program.cs"}:
            found.append(str(path))
            evidence.append(SourceEvidence(str(path), 1, "conventional entry-point filename"))
    if not found:
        return {"status": "abstain", "reason": "no_conventional_entrypoint_found", "answer": None, "evidence": []}
    return {"status": "answered", "answer": "Likely entry point(s): " + ", ".join(found),
            "evidence": [item.as_dict() for item in evidence]}
