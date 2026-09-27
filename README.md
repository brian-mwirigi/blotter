# Blotter

The invoice says KSh 18,000. The mobile-money log says KSh 13,500. The supplier was short KSh 4,500 because that receipt's date is a UNIX timestamp.

Blotter compares a shop's supplier invoices with a mobile-money statement and shows what is still unpaid. It does not send money or issue credit. Amani Hardware and both files are synthetic.

Composer 2.5, through the Cursor API, writes the matcher. The script runs in a sandbox with an import allowlist, a five-second timeout, and no API key in the child. A clean exit is not success: repeated ids and a tie-out must pass, or the error goes back. Three tries, then a labeled fallback. It cannot declare the shortfall. Brev was not used.

Submitted for the NVIDIA Brev Breakthrough Award, Thunders Engineering Excellence, and the Kredete Financial Inclusion Award. This is payment reconciliation. The open amount is KSh 4,500 on INV-100 against RCPT-100.

## Run

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

Open http://localhost:3000. Live demo is http://localhost:3000/demo.

Put `CURSOR_API_KEY` in a gitignored `.env`. Reconcile then calls Composer 2.5 only. Without the key, the sandbox runs a local script and the log says local.
