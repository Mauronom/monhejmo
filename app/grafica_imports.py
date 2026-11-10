from collections import defaultdict
from decimal import Decimal
from domain import calcular_punts, filtrar_moviments


class GraficaImports:
    """Dades de la gràfica d'imports acumulats per banc (i el total) dels moviments filtrats."""

    def __init__(self, sessio):
        self._sessio = sessio

    def execute(self, filtre):
        moviments = filtrar_moviments(self._sessio.actuals(), filtre)  # còpies, ordenades per data i banc
        acumulat = defaultdict(Decimal)
        for m in moviments:
            acumulat[m.banc] += m.import_
            m.balance = acumulat[m.banc]  # a la gràfica, el "saldo" és l'import acumulat
        return {
            "punts": calcular_punts(moviments),
            "etiqueta_x": "Data/Hora",
            "etiqueta_y": "Import Acumulat",
        }
