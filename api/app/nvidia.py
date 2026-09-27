"""Ask NVIDIA Build for a reconciliation script. Thinking stays off."""

import json
import os
import urllib.error
import urllib.request

from app.loop import ScriptModel

DEFAULT_MODEL = "deepseek-ai/deepseek-v4.1-flash"
ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"


def request_body(prompt: str, model: str) -> dict[str, object]:
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 2048,
        "chat_template_kwargs": {"thinking": False},
    }


class NvidiaModel(ScriptModel):
    def complete(self, prompt: str) -> str:
        key = os.environ.get("NVIDIA_API_KEY", "").strip()
        if not key:
            raise RuntimeError("NVIDIA_API_KEY is not set")
        model = os.environ.get("NVIDIA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        req = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(request_body(prompt, model)).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise RuntimeError(f"NVIDIA returned {exc.code}: {detail}") from exc
        message = payload["choices"][0]["message"]
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("NVIDIA returned an empty script")
        return content
