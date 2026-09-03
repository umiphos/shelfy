from fastapi import FastAPI

app = FastAPI(title="CATÁLOGO API")


@app.get("/")
def root():
    return {"message": "CATÁLOGO API funcionando"}


@app.get("/api/health")
def health():
    return {"status": "ok"}