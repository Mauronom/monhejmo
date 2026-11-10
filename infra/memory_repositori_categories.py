from domain import RepositoriCategories


class MemoryCategoriesRepo(RepositoriCategories):
    """Categories en memòria (per a tests i usos temporals)."""

    def __init__(self, cats=None):
        self.categories = cats if cats is not None else {}

    def get_all(self):
        return self.categories

    def save(self, name, texts):
        self.categories[name] = texts

    def delete(self, name):
        if name in self.categories:
            del self.categories[name]
            return True
        return False
