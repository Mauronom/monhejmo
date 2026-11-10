from domain import filtrar_moviments, calcular_stats, saldos_totals
from .resultat import ResultatMoviments


class FiltrarMoviments:
    """Filtra els moviments de la sessió i calcula el resum del període (incloent-hi les dates del filtre)."""

    def __init__(self, sessio):
        self._sessio = sessio

    def execute(self, filtre):
        tots = self._sessio.actuals()
        total_de = dict(zip(map(id, tots), saldos_totals(tots)))
        moviments = filtrar_moviments(tots, filtre)  # els mateixos objectes, sense copiar
        return ResultatMoviments(moviments, calcular_stats(moviments, filtre.data_inici, filtre.data_fi),
                                 [total_de[id(m)] for m in moviments])
