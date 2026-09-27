import subprocess

import pytest

from app.sandbox import ScriptRejected, run_script


def test_script_prints_its_result():
    completed = run_script("print('ok')\n")
    assert completed.returncode == 0
    assert completed.stdout.strip() == "ok"


def test_a_slow_script_is_stopped():
    with pytest.raises(subprocess.TimeoutExpired):
        run_script("while True:\n    pass\n", timeout=0.2)


def test_os_import_never_runs():
    with pytest.raises(ScriptRejected):
        run_script("import os\nos.system('echo no')\n")
