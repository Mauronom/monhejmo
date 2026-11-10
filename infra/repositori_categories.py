import json
from pathlib import Path
from domain import RepositoriCategories


class RepositoriCategoria(RepositoriCategories):
    """Categories desades a <directori>/categories.json. Si el fitxer no existeix, comença buit."""

    def __init__(self, directori):
        self.directori = Path(directori)
        self._fitxer = self.directori / "categories.json"
        self.categories = {}
        if self._fitxer.exists():
            self.categories = json.loads(self._fitxer.read_text(encoding="utf-8"))

    def get_all(self):
        return self.categories

    def save(self, name, texts):
        self.categories[name] = texts
        self._desar()

    def delete(self, name):
        if name not in self.categories:
            return False
        del self.categories[name]
        self._desar()
        return True

    def _desar(self):
        self.directori.mkdir(parents=True, exist_ok=True)
        self._fitxer.write_text(json.dumps(self.categories, indent=2, ensure_ascii=False), encoding="utf-8")
