from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.core.config import settings
from app.core.logging import logger
from app.db.session import engine
from app.db.base import Base

from app.api.routes.health import router as health_router
from app.api.routes.predictions import router as predictions_router

# Creează tabelele la bootstrap (Alembic recomandat ulterior pentru migrații)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

# UI static + template
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")
templates = Jinja2Templates(directory="app/ui/templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.app_name})

# API
app.include_router(health_router)
app.include_router(predictions_router)

logger.info("App started.")
