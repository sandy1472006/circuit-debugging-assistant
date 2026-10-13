"""
main.py - FastAPI application entry point for Circuit Debugging Assistant.
Integrates computer vision, analytical simulation, fault localization, and report generation.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.config import APP_NAME, APP_VERSION, APP_DESCRIPTION, UPLOAD_DIR, SAMPLE_DIR, REPORT_DIR, REFERENCE_DIR
from app.api.analysis import router as analysis_router
from app.api.reports import router as reports_router
from app.api.benchmarks import router as benchmarks_router
from app.api.assistant import router as assistant_router
from app.api.history import router as history_router

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(benchmarks_router)
app.include_router(assistant_router)
app.include_router(history_router)

# Mount static asset directories
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/samples", StaticFiles(directory=str(SAMPLE_DIR)), name="samples")
app.mount("/references", StaticFiles(directory=str(REFERENCE_DIR)), name="references")
app.mount("/reports_dir", StaticFiles(directory=str(REPORT_DIR)), name="reports_dir")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Circuit Debugging Assistant Backend Active</h1>")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "framework": "Mahajan et al. Hybrid Simulation & Evidence-Driven Framework"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
