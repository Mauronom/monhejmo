from decimal import Decimal
from .filtre import ordenar_moviments


def saldos_totals(moviments):
    """
    Per a cada moviment, la suma del darrer saldo conegut de cada banc just després d'aquest
    moviment (en ordre de data i banc; els bancs encara no vistos no compten).
    Retorna una llista en el mateix ordre que els moviments rebuts.
    """
    darrer, total_per_moviment = {}, {}
    for m in ordenar_moviments(moviments):
        darrer[m.banc] = m.balance
        total_per_moviment[id(m)] = sum(darrer.values(), Decimal(0))
    return [total_per_moviment[id(m)] for m in moviments]
