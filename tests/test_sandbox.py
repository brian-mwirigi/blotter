import subprocess

import pytest

from app.sandbox import run_script


def test_script_prints_its_result():
    completed = run_script("print('ok')\n")
    assert completed.returncode == 0
    assert completed.stdout.strip() == "ok"


def test_a_slow_script_is_stopped():
    with pytest.raises(subprocess.TimeoutExpired):
        run_script("import time\ntime.sleep(30)\n", timeout=0.2)
