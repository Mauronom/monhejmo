from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import NamedTuple


class PuntGrafica(NamedTuple):
    data: date
    ordre: int  # posició del moviment dins del dia i el banc (0, 1, 2...)
    saldo: Decimal
    banc: str
    concepte: str
    import_: Decimal


def calcular_punts(moviments):
    """
    Converteix moviments en PuntGrafica i afegeix, per a cada instant (data, ordre),
    un punt "Total" amb la suma de l'últim saldo conegut de cada banc.
    Retorna els punts ordenats per data, ordre i banc. A quina hora es dibuixa
    cada punt és cosa de la presentació.
    """
    comptadors = defaultdict(int)
    punts = []
    for m in moviments:
        clau = (m.data, m.banc)
        punts.append(PuntGrafica(m.data, comptadors[clau], m.balance, m.banc, m.concepte, m.import_))
        comptadors[clau] += 1

    per_instant = defaultdict(list)
    for p in punts:
        per_instant[(p.data, p.ordre)].append(p)

    ultim_saldo = {}  # banc -> últim saldo conegut (els bancs encara no vistos no compten)
    totals = []
    for data, ordre in sorted(per_instant):
        import_instant = Decimal(0)
        for p in per_instant[(data, ordre)]:
            ultim_saldo[p.banc] = p.saldo
            import_instant += p.import_
        totals.append(PuntGrafica(data, ordre, sum(ultim_saldo.values(), Decimal(0)), "Total", "Total", import_instant))

    return sorted(punts + totals, key=lambda p: (p.data, p.ordre, p.banc))
