# Blotter

The invoice says KSh 18,000. The phone says KSh 13,500. The shop is short KSh 4,500, and the receipt date that hid it is a UNIX timestamp.

Blotter puts a shop's supplier invoices next to a mobile-money statement and shows what is still unpaid. It does not send money. Amani Hardware and both files are synthetic.

Team Zero State. Brian Munene Mwirigi. Kenya.

| | |
| --- | --- |
| Live demo | https://blotterapp.vercel.app/demo |
| 90-second video | https://youtu.be/VUlZyA3qw-4 |
| Slides | https://gamma.app/docs/A-KSh-4500-gap-sat-hidden-until-Blotters-AI-found-it-after-its-ow-zjvun92e496o6m9 |
| Source | https://github.com/brian-mwirigi/blotter |

## The sample day

Four suppliers. One short payment. One reference used twice.

| Supplier | Invoice | Received | What happened |
| --- | --- | --- | --- |
| Lake Flour | 7,500 | 7,500 | Matched |
| Amani Hardware | 18,000 | 13,500 | Short 4,500. INV-100 vs RCPT-100 |
| Rift Cement | 22,000 | 22,000 | REF-102 used twice. First receipt kept |
| Coast Sugar | 4,500 | KSh 4,500 | Written as text. Still matched |

Invoiced 52,000. Received 47,500. Still open 4,500. Locked in `tests/test_hero.py`. Files: `data/supplier_invoices.csv`, `data/mock_mpesa_statement.json`.

Kenya’s 2016 KNBS MSME survey counted 7.41 million businesses, 5.85 million of them unlicensed. A hardware counter still matches invoices to M-Pesa messages by hand. Miss the KSh 4,500 and the shop has paid for stock it was never paid for.

## Engineering

Composer 2.5 fast writes the matcher. A second program decides whether that script counts. The model cannot set the shortfall.

| Control | What it enforces | Where |
| --- | --- | --- |
| Isolated child | The script runs in `python -I`. The allowlist is `json`, `csv`, `datetime`, `math`, `decimal`, `re`, `collections`, `io`. `eval`, `exec`, `open`, and `__import__` are rejected before the process starts. The child has no API key. Timeout is 5 seconds. | `api/app/sandbox.py` |
| Tie-out | A zero exit code is not acceptance. `repeated_ids` and `tie_out_problems` must pass, or the traceback is the next prompt. | `api/app/invariants.py` |
| Three attempts | The loop stops at 3. It does not keep retrying. | `api/app/loop.py` |
| Visible stop | The screen says Needs review. The rows come from the deterministic matcher. | `web/app/demo/run.tsx`, `api/app/match.py`, `api/app/run.py` |
| Locked money | The sample shortfall is asserted at KSh 4,500. | `tests/test_hero.py` |

On the sample, attempt 1 parses dates as `DD/MM/YYYY` and crashes on receipt `1773273600` at 27.7s. Attempt 2 is accepted at 58.3s. The headline is KSh 4,500 shortfall, INV-100 vs RCPT-100.

Thunders: `api/app/sandbox.py`, `api/app/loop.py`, `web/app/demo/run.tsx`. Kredete: `api/app/invariants.py`, `tests/test_hero.py`. Payment reconciliation. Kenya-based team. Brev was not used.

## Try the demo

Live: open https://blotterapp.vercel.app/demo. The sample files are already loaded. Check the consent box. Press Reconcile. Wait for the heal. The footer should read `composer-2.5 fast`.

Local, if that host cannot reach the reconcile service:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install fastapi==0.115.6 uvicorn==0.34.0 pydantic httpx python-multipart pytest cursor-sdk==1.0.32
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir api --host 127.0.0.1 --port 8000
```

```powershell
cd web
npm install
npm run dev
```

Open http://localhost:3000/demo. Same steps: sample loaded, consent, Reconcile.

Put `CURSOR_API_KEY` in a gitignored `.env`. Reconcile then calls Composer 2.5 only. Without the key, a local writer runs and the log says local. That is not a live model call. Do not commit the key.

```powershell
.\.venv\Scripts\python -m pytest
```

## What works, what does not

Works now: the upload, the generated script, the sandbox, the retry, the tie-out, the KSh 4,500 ledger, Needs review, and the consent gate.

Synthetic files only. No live M-Pesa and no bank. CSV invoices and JSON statements only. API cost is not measured. Run time under load is not measured. The retry cap is fixed at 3. Brev was not used.

Built at the hackathon: the matcher, the sandbox, the heal loop, the tie-out, the consent gate, and the demo. Reused libraries: Next.js, FastAPI, cursor-sdk.

## AI contribution

The model does three things. It writes executable Python for the columns in the upload. It reads a real runtime failure from the traceback. It writes a corrected script from that diagnosis. That is a closed loop, not a text reply that names the shortfall.

The accepted ledger is the one that passes the tie-out. The AI's output is not trusted on its own.

## Disclosure

Human oversight: if reconciliation cannot be resolved after 3 attempts, the demo marks the case “Needs review” and shows the deterministic ledger. That shortfall is not taken from the failed script. Safety: generated code runs in a subprocess with a restricted import allowlist and a 5-second timeout. Privacy: uploads are held for the request; the script is written in a temporary directory that is destroyed when the run finishes. Blotter does not store the files. Uploaded file contents are included in the AI model call required to generate the reconciliation script; Blotter does not control data retention on the model provider's side. Consent: users must explicitly acknowledge data handling and AI use before the reconcile action is enabled. That check is enforced in the interface. Bias: matching is a deterministic numerical comparison of invoice amounts to payment amounts. There is no demographic, behavioral, or identity input in the pipeline. Copyright: Blotter writes code and a ledger, not creative or copyrighted content.

## Next

Onboard a few real Kenyan shops and run the same loop on their invoices and statements. Add bank exports and another mobile-money provider. Keep the three-attempt cap until a low-confidence match can be flagged without guessing.
