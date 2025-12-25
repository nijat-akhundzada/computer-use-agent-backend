from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.messages import router as messages_router
from app.api.sessions import router as sessions_router
from app.api.streaming import router as streaming_router

app = FastAPI(title="Computer Use Backend")

app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(streaming_router)
app.include_router(messages_router)
app.include_router(history_router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
