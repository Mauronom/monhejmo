from dataclasses import dataclass
from decimal import Decimal
from typing import List
from domain import MovimentRecurrent, filtrar_moviments, detectar_recurrents, import_mensual_total


@dataclass(frozen=True)
class ResultatRecurrents:
    recurrents: List[MovimentRecurrent]
    import_mensual: Decimal  # dels que encara s'estan cobrant


class MovimentsRecurrents:
    """
    Despeses fixes (o, amb ingressos=True, ingressos fixos) dels moviments filtrats. Si encara
    s'estan cobrant es decideix a la data del darrer moviment de la sessió (no dels filtrats),
    o a la data fi del filtre si és anterior.
    """

    def __init__(self, sessio, config, ingressos=False):
        self._sessio = sessio
        self._config = config
        self._ingressos = ingressos

    def execute(self, filtre):
        tots = self._sessio.actuals()
        if not tots:
            return ResultatRecurrents([], Decimal(0))
        data_referencia = max(m.data for m in tots)
        if filtre.data_fi and filtre.data_fi < data_referencia:
            data_referencia = filtre.data_fi

        recurrents = detectar_recurrents(filtrar_moviments(tots, filtre), self._config.get_criteris(),
                                         data_referencia, ingressos=self._ingressos)
        return ResultatRecurrents(recurrents, import_mensual_total(recurrents))
