from fastapi import FastAPI

from app.api.debug_events import router as debug_router
from app.api.health import router as health_router
from app.api.sessions import router as sessions_router
from app.api.streaming import router as streaming_router

app = FastAPI(title="Computer Use Backend")

app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(streaming_router)
app.include_router(debug_router)
