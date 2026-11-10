import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from domain import RepositoriSuposits, Suposit, FixAcabat, PagamentEfectiu


def _data(text):
    return datetime.strptime(text, "%Y-%m-%d").date() if text else None


def _text(data):
    return data.isoformat() if data else None


class _JsonLlistaDePrevisio(RepositoriSuposits):
    """
    Una llista desada a config.json, a previsio.<clau> (o a <clau> si seccio és None).
    En desar, la resta del fitxer es manté.
    """
    seccio = "previsio"
    clau = None

    def __init__(self, config_path):
        self.config_path = Path(config_path)

    def _a_dict(self, element):
        raise NotImplementedError

    def _de_dict(self, dades):
        raise NotImplementedError

    def _llegir(self):
        if not self.config_path.exists():
            return {}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def _pare(self, config):
        return config.setdefault(self.seccio, {}) if self.seccio else config

    def get_all(self):
        return [self._de_dict(d) for d in self._pare(self._llegir()).get(self.clau, [])]

    def save_all(self, elements):
        config = self._llegir()
        self._pare(config)[self.clau] = [self._a_dict(e) for e in elements]
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


class JsonRepositoriSuposits(_JsonLlistaDePrevisio):
    """Supòsits a previsio.suposits de config.json."""
    clau = "suposits"

    def _a_dict(self, s):
        return {"concepte": s.concepte, "import": str(s.import_), "periodicitat": s.periodicitat,
                "inici": _text(s.data_inici), "fi": _text(s.data_fi)}

    def _de_dict(self, d):
        return Suposit(concepte=d["concepte"], import_=Decimal(str(d["import"])), periodicitat=d["periodicitat"],
                       data_inici=_data(d["inici"]), data_fi=_data(d.get("fi")))


class JsonRepositoriFixosAcabats(_JsonLlistaDePrevisio):
    """Fixos que s'acaben, a previsio.fixos_acabats de config.json."""
    clau = "fixos_acabats"

    def _a_dict(self, f):
        return {"banc": f.banc, "concepte": f.concepte, "fi": _text(f.data_fi)}

    def _de_dict(self, d):
        return FixAcabat(banc=d["banc"], concepte=d["concepte"], data_fi=_data(d["fi"]))


class JsonRepositoriPagamentsEfectiu(_JsonLlistaDePrevisio):
    """Pagaments fixos en efectiu, a pagaments_efectiu de config.json."""
    seccio = None
    clau = "pagaments_efectiu"

    def _a_dict(self, p):
        return {"concepte": p.concepte, "import": str(p.import_), "periodicitat": p.periodicitat,
                "inici": _text(p.data_inici), "fi": _text(p.data_fi)}

    def _de_dict(self, d):
        return PagamentEfectiu(concepte=d["concepte"], import_=Decimal(str(d["import"])),
                               periodicitat=d["periodicitat"], data_inici=_data(d["inici"]), data_fi=_data(d.get("fi")))


class MemoryRepositoriSuposits(RepositoriSuposits):
    """Llista en memòria (serveix per a supòsits, fixos que s'acaben i pagaments en efectiu)."""

    def __init__(self, elements=None):
        self._elements = list(elements or [])

    def get_all(self):
        return list(self._elements)

    def save_all(self, elements):
        self._elements = list(elements)
