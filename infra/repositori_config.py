from typing import List
import json
from datetime import datetime
from decimal import Decimal
from domain import (ConfigMovimentsFicticisRepo, ReglaMovimentFictici, ConfigRecurrentsRepo,
                    CriterisRecurrents, ConfigPrevisioRepo, ConfigPrevisio,
                    ConfigDespesesVariablesRepo, CriterisDespesesVariables)


class JsonConfigMovimentsFicticisRepo(ConfigMovimentsFicticisRepo):
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
    
    def get_regles(self) -> List[ReglaMovimentFictici]:
        config = self._load_config()
        regles = []
        for nom_regla, regla_data in config.get("moviments_ficticis", {}).items():
            regles.append(ReglaMovimentFictici(
                patrons=regla_data["patrons"],
                concepte_desti=regla_data["concepte_desti"],
                banc_desti=regla_data["banc_desti"],
                invertir_import=regla_data.get("invertir_import", True)
            ))
        return regles
    
    def get_moviments_inicials(self) -> List:
        from domain import Moviment  # Importació dinàmica per evitar dependències circulars
        
        config = self._load_config()
        moviments = []
        for mov_data in config.get("moviments_inicials", []):
            # Convertir string de data a datetime.date
            data = datetime.strptime(mov_data["data"], "%Y-%m-%d").date()
            moviments.append(Moviment(
                data=data,
                concepte=mov_data["concepte"],
                import_=mov_data["import"],
                balance=mov_data["balance"],
                banc=mov_data["banc"]
            ))
        return moviments
    
    def _load_config(self) -> dict:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

class MemoryConfigMovimentsFicticisRepo(ConfigMovimentsFicticisRepo):
    def __init__(self, regles: List[ReglaMovimentFictici] = None, moviments_inicials: List = None):
        self._regles = regles or []
        self._moviments_inicials = moviments_inicials or []
    
    def get_regles(self) -> List[ReglaMovimentFictici]:
        return self._regles.copy()
    
    def get_moviments_inicials(self) -> List:
        return self._moviments_inicials.copy()
    
    def afegir_regla(self, regla: ReglaMovimentFictici):
        self._regles.append(regla)
    
    def afegir_moviment_inicial(self, moviment):
        self._moviments_inicials.append(moviment)

class JsonConfigRecurrentsRepo(ConfigRecurrentsRepo):
    """Criteris de detecció de moviments fixos, a la secció `seccio` de config.json
    ("despeses_fixes" o "ingressos_fixos"). Sense la secció, els valors per defecte."""

    def __init__(self, config_path, seccio):
        self.config_path = config_path
        self.seccio = seccio

    def get_criteris(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                seccio = json.load(f).get(self.seccio, {})
        except FileNotFoundError:
            seccio = {}
        defecte = CriterisRecurrents()
        return CriterisRecurrents(
            min_mesos=seccio.get("min_mesos", defecte.min_mesos),
            max_carrecs_per_mes=seccio.get("max_carrecs_per_mes", defecte.max_carrecs_per_mes),
            max_variacio=seccio.get("max_variacio", defecte.max_variacio),
            incloure=tuple(seccio.get("incloure", ())),
            excloure=tuple(seccio.get("excloure", ())),
        )


class MemoryConfigRecurrentsRepo(ConfigRecurrentsRepo):
    def __init__(self, criteris=None):
        self._criteris = criteris or CriterisRecurrents()

    def get_criteris(self):
        return self._criteris


class JsonConfigPrevisioRepo(ConfigPrevisioRepo):
    """Configuració de la previsió, a la secció "previsio" de config.json. Sense la secció, per defecte."""

    def __init__(self, config_path):
        self.config_path = config_path

    def get_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                seccio = json.load(f).get("previsio", {})
        except FileNotFoundError:
            seccio = {}
        defecte = ConfigPrevisio()
        return ConfigPrevisio(
            horitzo_mesos=seccio.get("horitzo_mesos", defecte.horitzo_mesos),
            mesos_historic=seccio.get("mesos_historic", defecte.mesos_historic),
            bancs_exclosos=tuple(seccio.get("bancs_exclosos", defecte.bancs_exclosos)),
            categories_excloses=tuple(seccio.get("categories_excloses", defecte.categories_excloses)),
        )


class JsonConfigDespesesVariablesRepo(ConfigDespesesVariablesRepo):
    """Criteris de les despeses variables, a la secció "despeses_variables" de config.json.
    Sense la secció, els valors per defecte."""

    def __init__(self, config_path):
        self.config_path = config_path

    def get_criteris(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                seccio = json.load(f).get("despeses_variables", {})
        except FileNotFoundError:
            seccio = {}
        defecte = CriterisDespesesVariables()
        llindar = seccio.get("llindar_puntual")
        return CriterisDespesesVariables(
            llindar_puntual=defecte.llindar_puntual if llindar is None else Decimal(str(llindar)),
            categories_excloses=tuple(seccio.get("categories_excloses", defecte.categories_excloses)),
        )


class MemoryConfigDespesesVariablesRepo(ConfigDespesesVariablesRepo):
    def __init__(self, criteris=None):
        self._criteris = criteris or CriterisDespesesVariables()

    def get_criteris(self):
        return self._criteris


class MemoryConfigPrevisioRepo(ConfigPrevisioRepo):
    def __init__(self, config=None):
        self._config = config or ConfigPrevisio()

    def get_config(self):
        return self._config
