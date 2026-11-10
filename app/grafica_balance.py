from domain import calcular_punts, filtrar_moviments


class GraficaBalance:
    """Dades de la gràfica de saldo dels moviments filtrats: punts (PuntGrafica) per banc i el total."""

    def __init__(self, sessio):
        self._sessio = sessio

    def execute(self, filtre):
        moviments = filtrar_moviments(self._sessio.actuals(), filtre)
        return {
            "punts": calcular_punts(moviments),
            "etiqueta_x": "Data/Hora",
            "etiqueta_y": "Balanç",
        }
