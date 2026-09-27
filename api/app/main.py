from fastapi import FastAPI

app = FastAPI(title="LedgerHeal")


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"ok": True, "service": "ledgerheal"}
