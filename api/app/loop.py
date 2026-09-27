"""Ask for a script, run it, and hand the failure back. Three tries, then stop."""

import json
import subprocess
from dataclasses import dataclass

from app.invariants import repeated_ids, tie_out_problems
from app.sandbox import ScriptRejected, run_script
from app.schema import Invoice, Ledger, Receipt


@dataclass(frozen=True)
class Attempt:
    iteration: int
    status: str
    detail: str


@dataclass(frozen=True)
class HealResult:
    ledger: Ledger | None
    attempts: list[Attempt]
    mode: str


class ScriptModel:
    def complete(self, prompt: str) -> str:
        raise NotImplementedError


def extract_code(text: str) -> str:
    if "```" not in text:
        return text
    block = text.split("```", 2)[1]
    if block.startswith("python"):
        block = block[len("python") :]
    return block.strip() + "\n"


def heal(
    model: ScriptModel,
    task: str,
    *,
    invoices: list[Invoice] | None = None,
    receipts: list[Receipt] | None = None,
    max_tries: int = 3,
) -> HealResult:
    error = ""
    attempts: list[Attempt] = []
    for iteration in range(1, max_tries + 1):
        prompt = task if not error else f"{task}\n\nThe previous script failed:\n{error}"
        source = extract_code(model.complete(prompt))
        try:
            completed = run_script(source)
        except ScriptRejected as exc:
            error = str(exc)
            attempts.append(Attempt(iteration, "rejected", error))
            continue
        except subprocess.TimeoutExpired:
            error = "the script exceeded the time limit"
            attempts.append(Attempt(iteration, "timeout", error))
            continue
        if completed.returncode != 0:
            error = (completed.stderr or completed.stdout)[-2000:]
            attempts.append(Attempt(iteration, "crashed", error))
            continue
        try:
            ledger = Ledger.model_validate(json.loads(completed.stdout))
        except (json.JSONDecodeError, ValueError) as exc:
            error = f"output was not a ledger: {exc}"
            attempts.append(Attempt(iteration, "invalid", error))
            continue
        if invoices is not None and receipts is not None:
            problems = repeated_ids(ledger) + tie_out_problems(ledger, invoices, receipts)
            if problems:
                error = "\n".join(problems)
                attempts.append(Attempt(iteration, "unbalanced", error))
                continue
        attempts.append(Attempt(iteration, "accepted", "ledger accepted"))
        mode = "healed" if iteration > 1 else "clean"
        return HealResult(ledger, attempts, mode)
    return HealResult(None, attempts, "failed")
