"""Run a generated script only if its imports stay on the allowlist."""

import ast
import subprocess
import sys
import tempfile
from pathlib import Path

ALLOWED_IMPORTS = frozenset(
    {"pandas", "json", "csv", "datetime", "math", "decimal", "re", "collections"}
)
BANNED_CALLS = frozenset({"eval", "exec", "open", "__import__"})


class ScriptRejected(Exception):
    pass


def check_source(source: str) -> None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _require(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                raise ScriptRejected("relative import is not allowed")
            _require(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BANNED_CALLS:
                raise ScriptRejected(f"{func.id} is not allowed")


def _require(root: str) -> None:
    if root not in ALLOWED_IMPORTS:
        raise ScriptRejected(f"import {root} is not allowed")


def run_script(source: str, *, timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
    check_source(source)
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "reconcile.py"
        script.write_text(source, encoding="utf-8")
        return subprocess.run(
            [sys.executable, "-I", str(script)],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
