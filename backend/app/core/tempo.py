from datetime import UTC, datetime


def agora_utc() -> datetime:
    """Momento atual em UTC, sem tzinfo (naive).

    Substitui datetime.utcnow() (obsoleto desde o Python 3.12) mantendo o
    mesmo formato que ja esta no banco: o SQLite nao guarda fuso, entao um
    datetime com tzinfo voltaria do banco sem ele, e comparar os dois (ex.:
    expira_em < agora na checagem de sessao) daria TypeError.
    """
    return datetime.now(UTC).replace(tzinfo=None)
