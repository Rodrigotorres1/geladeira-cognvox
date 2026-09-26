"""Cria a unica usuaria do sistema ou redefine a senha dela.

Uso:
    python criar_usuario.py --nome "Maria" --email maria@exemplo.com
    python criar_usuario.py --redefinir-senha --email maria@exemplo.com

A senha e sempre pedida no terminal (nunca por argumento, para nao ficar no
historico do shell).
"""

import argparse
import getpass
import sys
from typing import Optional

from pydantic import ValidationError

from app.core.database import SessionLocal
from app.schemas.auth import RedefinicaoSenha, UsuarioCriar
from app.services import auth_service
from init_db import init_db


def pedir_senha() -> Optional[str]:
    senha = getpass.getpass("Senha: ")
    if senha != getpass.getpass("Confirme a senha: "):
        return None
    return senha


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cria a usuaria do sistema ou redefine a senha dela."
    )
    parser.add_argument("--nome", help="Nome da usuaria (obrigatorio ao criar)")
    parser.add_argument("--email", required=True, help="E-mail usado no login")
    parser.add_argument(
        "--redefinir-senha",
        action="store_true",
        help="Troca a senha da usuaria existente com esse e-mail",
    )
    args = parser.parse_args(argv)

    if not args.redefinir_senha and not args.nome:
        parser.error("--nome e obrigatorio ao criar a usuaria")

    senha = pedir_senha()
    if senha is None:
        print("As senhas nao conferem.", file=sys.stderr)
        return 1

    try:
        if args.redefinir_senha:
            dados_senha = RedefinicaoSenha(email=args.email, senha=senha)
        else:
            dados_usuario = UsuarioCriar(nome=args.nome, email=args.email, senha=senha)
    except ValidationError as erro:
        for detalhe in erro.errors():
            campo = ".".join(str(parte) for parte in detalhe["loc"])
            print(f"{campo}: {detalhe['msg']}", file=sys.stderr)
        return 1

    init_db()
    db = SessionLocal()
    try:
        if args.redefinir_senha:
            auth_service.redefinir_senha(db, dados_senha)
            print(f"Senha de {args.email} redefinida.")
        else:
            auth_service.registrar_usuario(db, dados_usuario)
            print(f"Usuaria {args.email} criada.")
    except auth_service.UsuarioJaExisteError:
        print(
            "Ja existe uma usuaria cadastrada. Use --redefinir-senha para trocar a senha.",
            file=sys.stderr,
        )
        return 1
    except auth_service.UsuarioNaoEncontradoError:
        print(f"Nenhuma usuaria com o e-mail {args.email}.", file=sys.stderr)
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
