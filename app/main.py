from fastapi import FastAPI

app = FastAPI(
    title="Concessional Loans Document Check API",
    version="0.1.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}
