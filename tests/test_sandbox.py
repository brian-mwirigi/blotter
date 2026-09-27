import subprocess

import pytest

from app.sandbox import ScriptRejected, child_env, run_script


def test_script_prints_its_result():
    completed = run_script("print('ok')\n")
    assert completed.returncode == 0
    assert completed.stdout.strip() == "ok"


def test_a_slow_script_is_stopped():
    with pytest.raises(subprocess.TimeoutExpired):
        run_script("while True:\n    pass\n", timeout=0.2)


def test_io_import_can_run():
    completed = run_script("import io\nprint(io.StringIO('ok').read())\n")
    assert completed.returncode == 0
    assert completed.stdout.strip() == "ok"


def test_pandas_import_never_runs():
    with pytest.raises(ScriptRejected, match="import pandas is not allowed"):
        run_script("import pandas\nprint('no')\n")


def test_os_import_never_runs():
    with pytest.raises(ScriptRejected):
        run_script("import os\nos.system('echo no')\n")


def test_api_key_is_absent_from_the_child_environment(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-value")
    env = child_env()
    assert "NVIDIA_API_KEY" not in env
    assert "secret-value" not in env.values()
