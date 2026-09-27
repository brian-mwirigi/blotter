import json
import urllib.request

from app.nvidia import NvidiaModel, request_body


def test_thinking_stays_off(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": "print('ok')\n"}}]}
            ).encode()

    def fake_urlopen(req, timeout=0):
        captured["body"] = json.loads(req.data.decode())
        captured["auth"] = req.get_header("Authorization")
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert NvidiaModel().complete("reconcile") == "print('ok')\n"
    assert captured["body"]["chat_template_kwargs"] == {"thinking": False}
    assert captured["body"]["max_tokens"] == 2048
    assert "reasoning_effort" not in captured["body"]
    assert captured["auth"] == "Bearer test-key"
    assert "test-key" not in json.dumps(captured["body"])
    assert request_body("x", "demo-model")["model"] == "demo-model"
