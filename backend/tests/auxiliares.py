from app.services.alertas import data_hoje


def mes_ano(meses: int = 0) -> str:
    """"MM/AAAA" a `meses` do mes atual (negativo = passado), no mesmo fuso
    que o backend usa para os alertas."""
    hoje = data_hoje()
    total = hoje.year * 12 + (hoje.month - 1) + meses
    return f"{total % 12 + 1:02d}/{total // 12}"
