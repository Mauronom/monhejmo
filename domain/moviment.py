from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Union
from .constants import CATEGORIA_PER_DEFECTE

@dataclass
class Moviment:
    data: date
    concepte: str
    import_: Union[Decimal, float, int, str]
    balance: Union[Decimal, float, int, str]
    banc: str
    categoria: str = CATEGORIA_PER_DEFECTE

    def __post_init__(self):
        # Convertir automàticament a Decimal
        if not isinstance(self.import_, Decimal):
            self.import_ = Decimal(str(self.import_))
        
        if not isinstance(self.balance, Decimal):
            self.balance = Decimal(str(self.balance))
            
    def clone(self):
        return Moviment(
            data=self.data,
            concepte=self.concepte,
            import_=self.import_,
            balance=self.balance,
            banc=self.banc,
            categoria=self.categoria
        )
    
    @staticmethod
    def clone_list(moviments):
        return [m.clone() for m in moviments]


def assignar_categories_a_moviments(moviments, categories_repo):
    """
    Assigna categories als moviments segons les paraules clau del repositori de categories.
    Es queda la primera categoria (en l'ordre del repositori) amb alguna paraula clau
    continguda al concepte, sense distingir majúscules. Si no n'hi ha cap, CATEGORIA_PER_DEFECTE.
    Retorna còpies; no modifica els moviments originals.
    """
    cats = categories_repo.get_all()
    moviments_resultats = []

    for m in moviments:
        moviment_copia = m.clone()
        concepte = moviment_copia.concepte.lower()
        moviment_copia.categoria = next(
            (cat for cat, paraules in cats.items() if any(p.lower() in concepte for p in paraules)),
            CATEGORIA_PER_DEFECTE,
        )
        moviments_resultats.append(moviment_copia)

    return moviments_resultats
