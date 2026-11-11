from domain import filtrar_moviments, detectar_recurrents, calcular_despeses_variables


class CalcularDespesesVariables:
    """
    Despeses variables dels moviments filtrats: sense les fixes, els traspassos ni les categories
    excloses, i amb les puntuals grosses a part. Les fixes es detecten amb tots els moviments de la
    sessió (no només els filtrats), perquè un filtre curt no deixi veure que una quota es repeteix.
    """

    def __init__(self, sessio, config_despeses_fixes, config):
        self._sessio = sessio
        self._config_despeses_fixes = config_despeses_fixes
        self._config = config

    def execute(self, filtre):
        tots = self._sessio.actuals()
        recurrents = detectar_recurrents(tots, self._config_despeses_fixes.get_criteris())
        return calcular_despeses_variables(filtrar_moviments(tots, filtre), recurrents,
                                           self._config.get_criteris(), filtre.data_inici, filtre.data_fi)
