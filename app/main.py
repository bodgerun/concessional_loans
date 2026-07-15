from fastapi import FastAPI

from app.api.routes import checks_router

app = FastAPI(
    title="Concessional Loans Document Check API",
    version="0.1.0",
)

app.include_router(checks_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}
