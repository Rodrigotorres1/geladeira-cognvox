import uuid

from sqlalchemy.orm import Session

from app.core.security import SESSION_DURATION, hash_password, verify_password
from app.core.tempo import agora_utc
from app.models.sessao import Sessao
from app.models.usuario import Usuario
from app.schemas.auth import RedefinicaoSenha, UsuarioCriar


class UsuarioJaExisteError(Exception):
    pass


class UsuarioNaoEncontradoError(Exception):
    pass


class CredenciaisInvalidasError(Exception):
    pass


def registrar_usuario(db: Session, dados: UsuarioCriar) -> Usuario:
    # O sistema tem uma unica usuaria: qualquer usuario ja cadastrado (mesmo
    # com outro e-mail) bloqueia a criacao. Trocar a senha e redefinir_senha.
    if db.query(Usuario.id).first() is not None:
        raise UsuarioJaExisteError()

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_password(dados.senha),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def redefinir_senha(db: Session, dados: RedefinicaoSenha) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario is None:
        raise UsuarioNaoEncontradoError()

    usuario.senha_hash = hash_password(dados.senha)
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
        expira_em=agora_utc() + SESSION_DURATION,
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
