from domain import (generar_moviments_ficticis, assignar_categories_a_moviments,
                    ordenar_moviments, calcular_stats, generar_moviments_efectiu, saldos_totals,
                    marcar_traspassos, moviments_assignats_targeta)
from .resultat import ResultatMoviments


class CarregarMoviments:
    """
    Llegeix els moviments d'un directori, hi afegeix els ficticis de la configuració, els
    pagaments fixos en efectiu (fins al darrer moviment llegit) i les compres de les targetes (amb
    la part assignada dels càrrecs), els categoritza, els desa a la sessió i retorna el resultat.
    """

    def __init__(self, font, config_ficticis, repositori_categories, sessio, repositori_pagaments_efectiu=None,
                 font_targetes=None):
        self._font = font
        self._config = config_ficticis
        self._repositori_categories = repositori_categories
        self._sessio = sessio
        self._pagaments_efectiu = repositori_pagaments_efectiu
        self._font_targetes = font_targetes

    def execute(self, directori):
        moviments = self._font.llegir(directori)
        llegits = list(moviments)
        if self._config is not None:
            moviments += generar_moviments_ficticis(
                moviments, self._config.get_regles(), self._config.get_moviments_inicials())
        if self._pagaments_efectiu is not None and llegits:
            moviments += generar_moviments_efectiu(self._pagaments_efectiu.get_all(), max(m.data for m in llegits))
        if self._font_targetes is not None:
            compres = self._font_targetes.llegir(directori)
            moviments += compres + moviments_assignats_targeta(compres)
        moviments = marcar_traspassos(assignar_categories_a_moviments(moviments, self._repositori_categories))
        moviments = ordenar_moviments(moviments)

        self._sessio.substituir(moviments)
        return ResultatMoviments(moviments, calcular_stats(moviments), saldos_totals(moviments))
