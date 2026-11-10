from abc import ABC, abstractmethod


class RepositoriCategories(ABC):
    """Port de les categories: {nom: [paraules clau]}, en un ordre estable (el de creació)."""

    @abstractmethod
    def get_all(self):
        """Retorna totes les categories com a {nom: [paraules clau]}."""

    @abstractmethod
    def save(self, name, texts):
        """Crea o substitueix la categoria amb aquestes paraules clau."""

    @abstractmethod
    def delete(self, name):
        """Elimina la categoria. Retorna True si existia."""
