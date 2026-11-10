from decimal import Decimal
from domain import filtrar_moviments


class GraficaCategories:
    """
    Dades de la gràfica de categories dels moviments filtrats: {categoria: import net}.
    Només hi surten les categories amb alguna despesa; els ingressos de la mateixa categoria hi resten.
    """

    def __init__(self, sessio):
        self._sessio = sessio

    def execute(self, filtre):
        moviments = filtrar_moviments(self._sessio.actuals(), filtre)
        # En l'ordre en què apareix la primera despesa de cada categoria (és l'ordre de les barres)
        net = dict.fromkeys((m.categoria for m in moviments if m.import_ < 0), Decimal(0))
        for m in moviments:
            if m.categoria in net:
                net[m.categoria] += m.import_
        return {categoria: float(import_) for categoria, import_ in net.items()}
