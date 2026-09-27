from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse

from app.env import load_env
from app.run import reconcile_events

load_env()

app = FastAPI(title="Blotter")


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"ok": True, "service": "blotter"}


@app.post("/reconcile")
async def reconcile(
    invoices: UploadFile = File(...),
    statement: UploadFile = File(...),
    pace: float = 0.35,
) -> StreamingResponse:
    csv_text = (await invoices.read()).decode("utf-8-sig")
    statement_text = (await statement.read()).decode("utf-8-sig")
    pace = min(max(pace, 0.0), 1.0)
    return StreamingResponse(
        reconcile_events(csv_text, statement_text, pace=pace),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
