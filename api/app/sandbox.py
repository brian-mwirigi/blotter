"""Run a generated script in a short-lived process. Later pulls tighten what it may import."""

import subprocess
import sys
import tempfile
from pathlib import Path


def run_script(source: str, *, timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
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
