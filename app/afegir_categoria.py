from domain import validar_nom_categoria


class AfegirCategoria:
    """Desa una categoria nova amb les seves paraules clau (si ja existeix, la sobreescriu)."""

    def __init__(self, repositori_categories):
        self._repositori_categories = repositori_categories

    def execute(self, nom, paraules_clau):
        validar_nom_categoria(nom)
        self._repositori_categories.save(nom, list(paraules_clau))
