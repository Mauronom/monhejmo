from abc import ABC, abstractmethod


class FontMoviments(ABC):
    """Port d'entrada de moviments: d'on es llegeixen (fitxers Norma 43, Excel, ...)."""

    @abstractmethod
    def llegir(self, directori):
        """Llegeix els moviments del directori i en retorna una llista de Moviment."""
