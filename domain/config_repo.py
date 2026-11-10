from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

@dataclass
class ReglaMovimentFictici:
    patrons: List[str]
    concepte_desti: str
    banc_desti: str
    invertir_import: bool = True

class ConfigMovimentsFicticisRepo(ABC):
    @abstractmethod
    def get_regles(self) -> List[ReglaMovimentFictici]:
        pass
    
    @abstractmethod
    def get_moviments_inicials(self) -> List:
        pass

class ConfigRecurrentsRepo(ABC):
    @abstractmethod
    def get_criteris(self):
        """Retorna els CriterisRecurrents."""


class ConfigPrevisioRepo(ABC):
    @abstractmethod
    def get_config(self):
        """Retorna la ConfigPrevisio."""


class RepositoriSuposits(ABC):
    """Supòsits de la previsió (Suposit o FixAcabat), en l'ordre en què s'han afegit."""

    @abstractmethod
    def get_all(self):
        """Retorna la llista de Suposit."""

    @abstractmethod
    def save_all(self, suposits):
        """Desa la llista sencera de Suposit."""
