from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.sessions import router as sessions_router

app = FastAPI(title="Computer Use Backend")

app.include_router(health_router)
app.include_router(sessions_router)
