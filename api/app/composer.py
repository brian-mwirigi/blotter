"""Composer 2.5 writes the script. The sandbox decides whether it counts."""

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path

MODEL = "composer-2.5"
LABEL = "composer-2.5 fast"


def _trust_local_scanner() -> None:
    """Let the bridge verify HTTPS when Avast is scanning TLS on this machine."""
    if os.environ.get("NODE_EXTRA_CA_CERTS"):
        return
    dest = Path(tempfile.gettempdir()) / "blotter-node-ca.pem"
    if not dest.is_file():
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "$cert = Get-ChildItem Cert:\\LocalMachine\\Root, Cert:\\CurrentUser\\Root |"
                " Where-Object { $_.Subject -like '*Avast Web/Mail Shield Root*' } |"
                " Select-Object -First 1; if (-not $cert) { exit 0 };"
                " $b64 = [Convert]::ToBase64String($cert.RawData, 'InsertLineBreaks');"
                " Set-Content -Path $env:DEST -Value \"-----BEGIN CERTIFICATE-----`n$b64`n-----END CERTIFICATE-----`n\" -Encoding ascii",
            ],
            env={**os.environ, "DEST": str(dest)},
            check=False,
            capture_output=True,
        )
    if dest.is_file() and dest.stat().st_size > 0:
        os.environ["NODE_EXTRA_CA_CERTS"] = str(dest)


def _fast_off(model: object) -> bool:
    params = getattr(model, "params", None)
    if params is None and isinstance(model, dict):
        params = model.get("params")
    if not params:
        return False
    for param in params:
        ident = getattr(param, "id", None)
        value = getattr(param, "value", None)
        if isinstance(param, dict):
            ident = param.get("id")
            value = param.get("value")
        if ident == "fast":
            return str(value).lower() != "true"
    return True


def model_id(model: object) -> str:
    if isinstance(model, str):
        return model
    ident = getattr(model, "id", None)
    if isinstance(ident, str):
        return ident
    if isinstance(model, dict):
        ident = model.get("id")
        return ident if isinstance(ident, str) else ""
    return ""


class ComposerModel:
    def complete(self, prompt: str) -> str:
        key = os.environ.get("CURSOR_API_KEY", "").strip()
        if not key:
            raise RuntimeError("CURSOR_API_KEY is not set")
        return asyncio.run(self._complete(prompt, key))

    async def _complete(self, prompt: str, key: str) -> str:
        from cursor_sdk import (
            AgentOptions,
            AsyncAgent,
            AsyncClient,
            CursorAgentError,
            LocalAgentOptions,
            ModelParameterValue,
            ModelSelection,
        )

        message = (
            prompt + "\n\nReply with only the Python source. Do not read, create, or edit files."
        )
        _trust_local_scanner()
        with tempfile.TemporaryDirectory(prefix="blotter-composer-") as cwd:
            local = LocalAgentOptions(cwd=cwd)
            try:
                client = await AsyncClient.launch_bridge(
                    workspace=cwd,
                    local=local,
                    client_timeout=240,
                )
                try:
                    result = await AsyncAgent.prompt(
                        message,
                        AgentOptions(
                            api_key=key,
                            model=ModelSelection(
                                id=MODEL,
                                params=(ModelParameterValue(id="fast", value="true"),),
                            ),
                            local=local,
                        ),
                        client=client,
                    )
                finally:
                    await client.aclose()
            except CursorAgentError as exc:
                message = getattr(exc, "message", None) or str(exc)
                raise RuntimeError(f"Composer did not start: {message}") from exc

        seen = model_id(getattr(result, "model", None))
        if seen != MODEL or _fast_off(getattr(result, "model", None)):
            raise RuntimeError(f"refused model {seen or 'unknown'}")
        if getattr(result, "status", "") != "finished":
            raise RuntimeError(f"Composer run {getattr(result, 'status', '') or 'failed'}")
        text = getattr(result, "result", None) or ""
        if not str(text).strip():
            raise RuntimeError("Composer returned an empty script")
        return str(text)
