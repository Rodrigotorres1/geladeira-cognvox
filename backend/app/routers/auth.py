from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    SESSION_COOKIE_NAME,
    cookie_is_secure,
    get_current_user,
    sign_session_id,
    unsign_session_id,
)
from app.models.usuario import Usuario
from app.schemas.auth import UsuarioLogin, UsuarioOut, UsuarioRegistro
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registro(dados: UsuarioRegistro, db: Session = Depends(get_db)):
    try:
        return auth_service.registrar_usuario(db, dados)
    except auth_service.EmailJaCadastradoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email ja cadastrado"
        )


@router.post("/login", response_model=UsuarioOut)
def login(dados: UsuarioLogin, response: Response, db: Session = Depends(get_db)):
    try:
        usuario = auth_service.autenticar_usuario(db, dados.email, dados.senha)
    except auth_service.CredenciaisInvalidasError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha invalidos"
        )

    sessao = auth_service.criar_sessao(db, usuario)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=sign_session_id(sessao.id),
        httponly=True,
        samesite="lax",
        secure=cookie_is_secure(),
        max_age=int((sessao.expira_em - sessao.criado_em).total_seconds()),
        path="/",
    )
    return usuario


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
):
    if session_id is not None:
        sessao_id = unsign_session_id(session_id)
        if sessao_id is not None:
            auth_service.encerrar_sessao(db, sessao_id)

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


@router.get("/me", response_model=UsuarioOut)
def me(usuario_atual: Usuario = Depends(get_current_user)):
    return usuario_atual
