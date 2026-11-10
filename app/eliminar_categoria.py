class EliminarCategoria:
    """Elimina una categoria. Retorna True si existia i s'ha eliminat."""

    def __init__(self, repositori_categories):
        self._repositori_categories = repositori_categories

    def execute(self, nom):
        return self._repositori_categories.delete(nom)
