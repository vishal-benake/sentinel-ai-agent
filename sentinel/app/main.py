
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.incidents import router as incidents_router
from app.api.ingestion import router as ingestion_router
from app.api.investigations import router as investigations_router
from app.database.database import init_db


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered incident investigation and resolution platform",
)

app.include_router(incidents_router)
app.include_router(ingestion_router)
app.include_router(investigations_router)

init_db()

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "sentinel-api",
    }
