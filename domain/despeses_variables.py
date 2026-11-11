from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
from .pagaments_efectiu import CONCEPTE_EFECTIU_ASSIGNAT
from .recurrents import DIES_PER_MES, CENTIMS
from .targetes import CONCEPTE_TARGETA_ASSIGNADA
from .traspassos import CATEGORIA_TRASPAS


# Moviments positius que no són ingressos: treuen d'una categoria la part que ja surt desglossada
CONCEPTES_ASSIGNATS = (CONCEPTE_EFECTIU_ASSIGNAT, CONCEPTE_TARGETA_ASSIGNADA)


@dataclass(frozen=True)
class CriterisDespesesVariables:
    """
    - llindar_puntual: les despeses de més d'aquest import van a part, com a puntuals.
    - categories_excloses: categories que no compten (els traspassos no compten mai).
    """
    llindar_puntual: Decimal = Decimal(1000)
    categories_excloses: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DespesaCategoria:
    """La despesa variable d'una categoria. Els imports són positius."""
    categoria: str
    total: Decimal
    mensual: Decimal
    moviments: int


@dataclass(frozen=True)
class DespesesVariables:
    per_categoria: List[DespesaCategoria]  # de més a menys despesa
    puntuals: List                         # els moviments, de la despesa més grossa a la més petita
    total: Decimal                         # sense les puntuals
    mensual: Decimal
    total_puntuals: Decimal
    mesos: Decimal                         # durada del període


def _mesos(moviments, data_inici, data_fi):
    if not moviments:
        return Decimal(0)
    d_ini = min([m.data for m in moviments] + ([data_inici] if data_inici else []))
    d_fi = max([m.data for m in moviments] + ([data_fi] if data_fi else []))
    return Decimal((d_fi - d_ini).days + 1) / DIES_PER_MES


def _arrodonir(valor):
    return valor.quantize(CENTIMS, ROUND_HALF_UP)


def calcular_despeses_variables(moviments, recurrents, criteris, data_inici: Optional[date] = None,
                                data_fi: Optional[date] = None):
    """
    Despesa del dia a dia: la dels moviments que no són de cap despesa fixa (`recurrents`), ni
    traspassos entre comptes, ni de les categories excloses. Les de més de llindar_puntual van a
    part. La part de les retirades d'efectiu assignada a pagaments fixos i la dels càrrecs de la
    targeta desglossada en compres (CONCEPTES_ASSIGNATS) es resta de la seva categoria. El període
    (per a la mitjana mensual) va de la data més antiga (moviment o data_inici) a la més recent
    (moviment o data_fi).
    """
    moviments = list(moviments)
    mesos = _mesos(moviments, data_inici, data_fi)
    dels_fixos = {id(m) for r in recurrents for m in r.moviments}
    excloses = set(criteris.categories_excloses) | {CATEGORIA_TRASPAS}

    totals = defaultdict(lambda: Decimal(0))
    nombre = defaultdict(int)
    puntuals = []
    for m in moviments:
        if id(m) in dels_fixos or m.categoria in excloses:
            continue
        if m.import_ < 0 and -m.import_ > criteris.llindar_puntual:
            puntuals.append(m)
        elif m.import_ < 0:
            totals[m.categoria] -= m.import_
            nombre[m.categoria] += 1
        elif m.concepte in CONCEPTES_ASSIGNATS:
            totals[m.categoria] -= m.import_

    def mensual(total):
        return _arrodonir(total / mesos) if mesos else Decimal(0)

    per_categoria = sorted(
        (DespesaCategoria(categoria, total, mensual(total), nombre[categoria])
         for categoria, total in totals.items() if total > 0),
        key=lambda c: (-c.total, c.categoria))
    total = sum((c.total for c in per_categoria), Decimal(0))
    return DespesesVariables(
        per_categoria=per_categoria,
        puntuals=sorted(puntuals, key=lambda m: (m.import_, m.data)),
        total=total,
        mensual=mensual(total),
        total_puntuals=-sum((m.import_ for m in puntuals), Decimal(0)),
        mesos=_arrodonir(mesos),
    )
