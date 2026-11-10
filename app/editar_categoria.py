from domain import validar_nom_categoria


class EditarCategoria:
    """Substitueix les paraules clau d'una categoria (si no existeix, la crea)."""

    def __init__(self, repositori_categories):
        self._repositori_categories = repositori_categories

    def execute(self, nom, paraules_clau):
        validar_nom_categoria(nom)
        self._repositori_categories.save(nom, list(paraules_clau))
