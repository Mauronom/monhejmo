class CategoriaInvalida(ValueError):
    """La categoria no es pot desar (per exemple, no té nom)."""


def validar_nom_categoria(nom):
    if not nom or not nom.strip():
        raise CategoriaInvalida("La categoria ha de tenir un nom.")


def parsejar_paraules_clau(text):
    """Converteix "a, b ,c" en ["a", "b", "c"], descartant els elements buits."""
    if not text:
        return []
    return [p.strip() for p in text.split(",") if p.strip()]
