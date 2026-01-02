from fastapi import FastAPI

app = FastAPI(title="AI Platform")

@app.get("/health")
def health():
    return {"status": "ok"}
