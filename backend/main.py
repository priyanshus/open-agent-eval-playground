import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat_controller import router as chat_router
from backend.api.flight_controller import router as flight_router

_CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").strip().split(",")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)
app.include_router(flight_router)
