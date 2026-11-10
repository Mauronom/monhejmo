from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
from .moviment import Moviment
from .previsio import PERIODICITATS, SupositInvalid, dates_periodiques

BANC_EFECTIU = "EFECTIU"
# Concepte de la part de les retirades que queda explicada per un pagament (categoria "efectiu")
CONCEPTE_EFECTIU_ASSIGNAT = "RETIRADA EFECTIVO ASSIGNADA"


@dataclass(frozen=True)
class PagamentEfectiu:
    """Un pagament fix que es fa en efectiu, amb diners de les retirades del caixer."""
    concepte: str
    import_: Decimal  # el que es paga, en positiu
    periodicitat: str  # una de PERIODICITATS
    data_inici: date
    data_fi: Optional[date] = None


def validar_pagament_efectiu(pagament):
    if not pagament.concepte.strip():
        raise SupositInvalid("Cal un concepte.")
    if pagament.import_ <= 0:
        raise SupositInvalid("L'import ha de ser el que es paga, en positiu.")
    if pagament.periodicitat not in PERIODICITATS:
        raise SupositInvalid(f"Periodicitat desconeguda: {pagament.periodicitat}.")
    if pagament.data_fi and pagament.data_fi < pagament.data_inici:
        raise SupositInvalid("La data de fi és anterior a la d'inici.")


def _dates(pagament, data_fi):
    fi = min(data_fi, pagament.data_fi) if pagament.data_fi else data_fi
    return dates_periodiques(pagament.data_inici, pagament.periodicitat, fi)


def generar_moviments_efectiu(pagaments, data_fi):
    """
    Moviments del compte EFECTIU fins a data_fi: per a cada pagament, la despesa
    "<concepte> (efectiu)" i la mateixa quantitat en positiu com a CONCEPTE_EFECTIU_ASSIGNAT, que
    treu aquesta part de la categoria de les retirades. Tots dos amb saldo 0: el total no canvia.
    """
    moviments = []
    for p in pagaments:
        for data in _dates(p, data_fi):
            moviments.append(Moviment(data, f"{p.concepte} (efectiu)", -p.import_, 0, BANC_EFECTIU))
            moviments.append(Moviment(data, CONCEPTE_EFECTIU_ASSIGNAT, p.import_, 0, BANC_EFECTIU))
    return sorted(moviments, key=lambda m: m.data)
