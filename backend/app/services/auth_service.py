import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import SESSION_DURATION, hash_password, verify_password
from app.models.sessao import Sessao
from app.models.usuario import Usuario
from app.schemas.auth import UsuarioRegistro


class EmailJaCadastradoError(Exception):
    pass


class CredenciaisInvalidasError(Exception):
    pass


def registrar_usuario(db: Session, dados: UsuarioRegistro) -> Usuario:
    email_existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if email_existente is not None:
        raise EmailJaCadastradoError()

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_password(dados.senha),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def autenticar_usuario(db: Session, email: str, senha: str) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not verify_password(senha, usuario.senha_hash):
        raise CredenciaisInvalidasError()
    return usuario


def criar_sessao(db: Session, usuario: Usuario) -> Sessao:
    sessao = Sessao(
        usuario_id=usuario.id,
        expira_em=datetime.utcnow() + SESSION_DURATION,
    )
    db.add(sessao)
    db.commit()
    db.refresh(sessao)
    return sessao


def encerrar_sessao(db: Session, sessao_id: uuid.UUID) -> None:
    sessao = db.get(Sessao, sessao_id)
    if sessao is not None:
        db.delete(sessao)
        db.commit()
