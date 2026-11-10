from domain import validar_suposit, validar_fix_acabat, validar_pagament_efectiu


class LlistarSuposits:
    def __init__(self, repositori):
        self._repositori = repositori

    def execute(self):
        return self._repositori.get_all()


class AfegirSuposit:
    """Afegeix un supòsit al final. Llança SupositInvalid si no és vàlid."""
    _validar = staticmethod(validar_suposit)

    def __init__(self, repositori):
        self._repositori = repositori

    def execute(self, suposit):
        self._validar(suposit)
        self._repositori.save_all(self._repositori.get_all() + [suposit])


class EliminarSuposit:
    """Elimina el supòsit de la posició indicada. Retorna False si no n'hi ha cap."""

    def __init__(self, repositori):
        self._repositori = repositori

    def execute(self, posicio):
        suposits = self._repositori.get_all()
        if not 0 <= posicio < len(suposits):
            return False
        del suposits[posicio]
        self._repositori.save_all(suposits)
        return True


# Els fixos que s'acaben són supòsits d'un altre tipus, amb el seu repositori
class LlistarFixosAcabats(LlistarSuposits):
    pass


class AcabarFix(AfegirSuposit):
    """Afegeix un FixAcabat. Llança SupositInvalid si no és vàlid."""
    _validar = staticmethod(validar_fix_acabat)


class EliminarFixAcabat(EliminarSuposit):
    pass


# Els pagaments fixos en efectiu es gestionen igual, amb el seu repositori
class LlistarPagamentsEfectiu(LlistarSuposits):
    pass


class AfegirPagamentEfectiu(AfegirSuposit):
    """Afegeix un PagamentEfectiu. Llança SupositInvalid si no és vàlid."""
    _validar = staticmethod(validar_pagament_efectiu)


class EliminarPagamentEfectiu(EliminarSuposit):
    pass
