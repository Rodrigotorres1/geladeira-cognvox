from typing import Annotated, Any, Optional

from pydantic import BeforeValidator


def _vazio_para_none(valor: Any) -> Any:
    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None
    return valor


# Campo de texto opcional vindo de formulario: o frontend manda "" quando o
# input fica em branco, e aqui isso vira None em vez de gravar string vazia.
TextoOpcional = Annotated[Optional[str], BeforeValidator(_vazio_para_none)]
