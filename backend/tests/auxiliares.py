from datetime import timedelta

from app.services.alertas import data_hoje


def dias(n: int) -> str:
    """Data ISO a n dias de hoje (negativo = passado), no mesmo fuso que o
    backend usa para os alertas."""
    return (data_hoje() + timedelta(days=n)).isoformat()
