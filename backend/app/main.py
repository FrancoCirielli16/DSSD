from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, emergencias, lotes, ofertas
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.seed import seed_users


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()
    yield


app = FastAPI(title="RescueSync API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(emergencias.router)
app.include_router(lotes.router)
app.include_router(ofertas.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
