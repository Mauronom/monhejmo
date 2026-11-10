class LlistarCategories:
    """Retorna una còpia de totes les categories: {nom: [paraules clau]}, en l'ordre del repositori."""

    def __init__(self, repositori_categories):
        self._repositori_categories = repositori_categories

    def execute(self):
        return {nom: list(paraules) for nom, paraules in self._repositori_categories.get_all().items()}
