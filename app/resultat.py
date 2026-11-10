from dataclasses import dataclass, field
from decimal import Decimal
from typing import List
from domain import Moviment, Resum


@dataclass
class ResultatMoviments:
    """
    Moviments a mostrar, el resum (total, diari, mensual) del període i, per a cada moviment,
    el saldo total de tots els bancs en aquell moment (calculat amb tots els moviments).
    """
    moviments: List[Moviment]
    resum: Resum
    saldos_totals: List[Decimal] = field(default_factory=list)
