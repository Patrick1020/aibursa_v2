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
from app.api.routes.market import router as market_router
from app.api.routes.ml import router as ml_router
from app.api.routes.universe import router as universe_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

# Static & templates
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")
templates = Jinja2Templates(directory="app/ui/templates")

from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def unhandled_exc(request: Request, exc: Exception):
    # Pentru rutele HTML vrem pagina standard de eroare; limităm handlerul la /api/*
    if request.url.path.startswith("/api/"):
        # în dev poți include str(exc) dacă vrei mai mult context
        return JSONResponse(status_code=500, content={"ok": False, "error": "Internal Server Error"})
    # altfel, lasă FastAPI/Starlette să afișeze pagina HTML
    raise exc


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.app_name})

@app.get("/fast-trade", response_class=HTMLResponse)
def fast_trade(request: Request):
    return templates.TemplateResponse("fasttrade.html", {"request": request, "app_name": settings.app_name})

# API
app.include_router(health_router)
app.include_router(predictions_router)
app.include_router(market_router)
app.include_router(universe_router)
app.include_router(ml_router)


logger.info("UI loaded (enterprise layout).")
