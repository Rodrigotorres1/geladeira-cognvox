import uuid
from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import Cookie, Depends, HTTPException, status
from itsdangerous import BadSignature, URLSafeSerializer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.sessao import Sessao
from app.models.usuario import Usuario

settings = get_settings()

SESSION_COOKIE_NAME = "session_id"
SESSION_DURATION = timedelta(days=7)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Assina o id da sessao com a SECRET_KEY: o cookie nunca guarda dados do
# usuario, so esse id assinado. Sem a SECRET_KEY nao da pra forjar um valor
# valido, e qualquer alteracao no cookie invalida a assinatura.
_serializer = URLSafeSerializer(settings.secret_key, salt="session-cookie")


def hash_password(senha: str) -> str:
    return pwd_context.hash(senha)


def verify_password(senha: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha, senha_hash)


def sign_session_id(session_id: uuid.UUID) -> str:
    return _serializer.dumps(str(session_id))


def unsign_session_id(cookie_value: str) -> Optional[uuid.UUID]:
    try:
        raw = _serializer.loads(cookie_value)
        return uuid.UUID(raw)
    except (BadSignature, ValueError):
        return None


def cookie_is_secure() -> bool:
    return settings.environment != "local"


# Local: backend e frontend rodam os dois em localhost (portas diferentes,
# mas mesmo "site" para fins de SameSite) — "lax" já basta e nem exige
# Secure, o que evita precisar de HTTPS local. Fora de local (Render +
# Vercel, dominios diferentes): e uma requisicao cross-site de verdade, e
# navegadores so mandam cookie cross-site com SameSite="none" — que por sua
# vez exige Secure=True (cookie_is_secure() ja liga isso fora de "local").
def cookie_samesite() -> Literal["lax", "none"]:
    return "lax" if settings.environment == "local" else "none"


def get_current_user(
    session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> Usuario:
    nao_autenticado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nao autenticado",
    )

    if session_id is None:
        raise nao_autenticado

    sessao_id = unsign_session_id(session_id)
    if sessao_id is None:
        raise nao_autenticado

    sessao = db.get(Sessao, sessao_id)
    if sessao is None or sessao.expira_em < datetime.utcnow():
        raise nao_autenticado

    usuario = db.get(Usuario, sessao.usuario_id)
    if usuario is None:
        raise nao_autenticado

    return usuario
