import sys
import types

import pytest

from app.composer import LABEL, MODEL, ComposerModel
from app.run import choose_model


def _install_sdk(monkeypatch, result):
    captured = {}

    class AsyncClient:
        @staticmethod
        async def launch_bridge(**kwargs):
            captured["cwd"] = kwargs["workspace"]
            return _Client()

    class _Client:
        async def aclose(self):
            captured["closed"] = True

    class AsyncAgent:
        @staticmethod
        async def prompt(message, options, *, client):
            captured["message"] = message
            captured["model"] = options.model
            captured["key"] = options.api_key
            captured["client"] = client
            return result

    class AgentOptions:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class LocalAgentOptions:
        def __init__(self, cwd):
            self.cwd = cwd

    class ModelParameterValue:
        def __init__(self, id, value):
            self.id = id
            self.value = value

    class ModelSelection:
        def __init__(self, id, params=()):
            self.id = id
            self.params = params

    class CursorAgentError(Exception):
        def __init__(self, message):
            super().__init__(message)
            self.message = message

    fake = types.ModuleType("cursor_sdk")
    fake.AsyncClient = AsyncClient
    fake.AsyncAgent = AsyncAgent
    fake.AgentOptions = AgentOptions
    fake.LocalAgentOptions = LocalAgentOptions
    fake.ModelParameterValue = ModelParameterValue
    fake.ModelSelection = ModelSelection
    fake.CursorAgentError = CursorAgentError
    monkeypatch.setitem(sys.modules, "cursor_sdk", fake)
    return captured


def test_prompt_is_locked_to_composer(monkeypatch):
    class Result:
        status = "finished"
        result = "print('ok')\n"
        model = type("Selection", (), {"id": MODEL})()

    captured = _install_sdk(monkeypatch, Result())
    monkeypatch.setenv("CURSOR_API_KEY", "cursor-test")
    assert ComposerModel().complete("write the matcher") == "print('ok')\n"
    assert captured["model"].id == "composer-2.5"
    assert captured["model"].params[0].id == "fast"
    assert captured["model"].params[0].value == "true"
    assert captured["key"] == "cursor-test"
    assert captured["cwd"]
    assert captured["closed"] is True
    assert "cursor-test" not in captured["message"]


def test_another_model_is_refused(monkeypatch):
    class Result:
        status = "finished"
        result = "print('ok')\n"
        model = type("Selection", (), {"id": "gpt-5"})()

    _install_sdk(monkeypatch, Result())
    monkeypatch.setenv("CURSOR_API_KEY", "cursor-test")
    with pytest.raises(RuntimeError, match="refused model gpt-5"):
        ComposerModel().complete("write the matcher")


def test_cursor_key_beats_the_nvidia_key(monkeypatch):
    monkeypatch.setenv("CURSOR_API_KEY", "cursor-test")
    monkeypatch.setenv("NVIDIA_API_KEY", "nv-test")
    _model, engine, name = choose_model()
    assert engine == "cursor"
    assert name == LABEL == "composer-2.5 fast"
