import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# Usados so pelo criar_usuario.py: nao existe mais cadastro pela API.
class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=1)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)


class RedefinicaoSenha(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str = Field(max_length=72)


class UsuarioOut(BaseModel):
    id: uuid.UUID
    nome: str
    email: EmailStr
    criado_em: datetime

    model_config = {"from_attributes": True}
