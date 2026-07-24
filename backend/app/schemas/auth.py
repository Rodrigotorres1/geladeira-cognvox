import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UsuarioRegistro(BaseModel):
    nome: str = Field(min_length=1)
    email: EmailStr
    senha: str = Field(min_length=8)


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str


class UsuarioOut(BaseModel):
    id: uuid.UUID
    nome: str
    email: EmailStr
    criado_em: datetime

    model_config = {"from_attributes": True}
