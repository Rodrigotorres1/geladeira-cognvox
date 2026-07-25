from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, itens, movimentacoes, relatorios
from init_db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Sistema de Controle de Estoque de Geladeira", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(itens.router)
app.include_router(movimentacoes.router)
app.include_router(relatorios.router)


@app.get("/health")
def health():
    return {"status": "ok"}
