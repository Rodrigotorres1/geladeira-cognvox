from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.validacao import tratar_erro_validacao
from app.routers import auth, lotes, movimentacoes, tipos
from init_db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Controle de Cilindros de Oxigenio", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 422 de validacao com mensagens em portugues (o padrao do Pydantic e ingles).
app.add_exception_handler(RequestValidationError, tratar_erro_validacao)


app.include_router(auth.router)
app.include_router(tipos.router)
app.include_router(lotes.router)
app.include_router(movimentacoes.router)


@app.get("/health")
def health():
    return {"status": "ok"}
