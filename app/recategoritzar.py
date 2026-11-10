from domain import (assignar_categories_a_moviments, ordenar_moviments, calcular_stats, saldos_totals,
                    marcar_traspassos)
from .resultat import ResultatMoviments


class Recategoritzar:
    """Torna a assignar les categories (paraules clau actuals i traspassos) als moviments de la sessió."""

    def __init__(self, sessio, repositori_categories):
        self._sessio = sessio
        self._repositori_categories = repositori_categories

    def execute(self):
        moviments = marcar_traspassos(assignar_categories_a_moviments(self._sessio.actuals(),
                                                                      self._repositori_categories))
        moviments = ordenar_moviments(moviments)
        self._sessio.substituir(moviments)
        return ResultatMoviments(moviments, calcular_stats(moviments), saldos_totals(moviments))
