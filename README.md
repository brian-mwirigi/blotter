# Blotter

The invoice says KSh 18,000. The mobile-money log says KSh 13,500. The supplier was short KSh 4,500.

This repository is the scaffold for that payments check. The matcher, the sandbox, and the dashboard arrive in later pull requests. Nothing here moves money.

## Layout

- `api/` holds the FastAPI service. `GET /health` is the only route so far.
- `web/` holds the Next.js app. The first screen states the shortfall.
- `data/` is where the synthetic invoice and statement files will go.
- `tests/` is where the ledger checks will go.

## Run the API

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -r api\requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir api --reload
```

## Run the web app

```powershell
cd web
npm install
npm run dev
```

Keep `NVIDIA_API_KEY` in a local `.env`. That file is gitignored.
