from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Resum:
    total: Decimal
    diari: Decimal
    mensual: Decimal


def calcular_stats(moviments, date_inici=None, date_fi=None):
    """
    Retorna un Resum (total, diari, mensual) amb valors Decimal.
    El període va de la data més antiga (moviment o date_inici) a la més recent (moviment o date_fi).
    """
    if not moviments:
        return Resum(Decimal(0), Decimal(0), Decimal(0))

    moviments = sorted(moviments, key=lambda m: m.data)
    total = sum((m.import_ for m in moviments), Decimal(0))

    d_ini = min(moviments[0].data, date_inici) if date_inici else moviments[0].data
    d_fi = max(moviments[-1].data, date_fi) if date_fi else moviments[-1].data
    dies = (d_fi - d_ini).days + 1

    diari = total / dies
    mensual = diari * 30
    return Resum(total, diari, mensual)
