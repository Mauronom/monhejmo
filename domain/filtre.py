from dataclasses import dataclass
from datetime import date
from typing import Optional
from .categories import es_dins


@dataclass(frozen=True)
class FiltreMoviments:
    """Criteris de filtre. Els camps buits (None o "") no filtren. La categoria inclou les seves subcategories."""
    text: str = ""
    data_inici: Optional[date] = None
    data_fi: Optional[date] = None
    categoria: Optional[str] = None


def ordenar_moviments(moviments):
    return sorted(moviments, key=lambda m: (m.data, m.banc))


def filtrar_moviments(moviments, filtre):
    """Retorna els moviments que compleixen el filtre, ordenats per data i banc."""
    text = (filtre.text or "").lower()
    if filtre.data_inici and filtre.data_fi and filtre.data_inici > filtre.data_fi:
        return []

    def compleix(m):
        return ((not text or text in m.concepte.lower())
                and (not filtre.categoria or es_dins(m.categoria, filtre.categoria))
                and (not filtre.data_inici or m.data >= filtre.data_inici)
                and (not filtre.data_fi or m.data <= filtre.data_fi))

    return ordenar_moviments(m for m in moviments if compleix(m))
