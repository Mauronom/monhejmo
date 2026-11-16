class CategoriaInvalida(ValueError):
    """La categoria no es pot desar (per exemple, no té nom)."""


# Les categories formen un arbre: "casa/subministraments/llum" és dins de "casa/subministraments",
# que és dins de "casa". Cada moviment té la categoria del nivell més concret que se'n sap.
SEPARADOR = "/"


def validar_nom_categoria(nom):
    if not nom or not nom.strip():
        raise CategoriaInvalida("La categoria ha de tenir un nom.")
    if any(not nivell.strip() for nivell in nom.split(SEPARADOR)):
        raise CategoriaInvalida(f"Cap nivell de la categoria pot ser buit (separa'ls amb \"{SEPARADOR}\").")


def es_dins(categoria, node):
    """Si la categoria és el node o un dels seus descendents."""
    return categoria == node or categoria.startswith(node + SEPARADOR)


def es_dins_algun(categoria, nodes):
    return any(es_dins(categoria, node) for node in nodes)


def categoria_a_nivell(categoria, nivell):
    """El node de la categoria a aquest nivell (1 és l'arrel); si la categoria és menys profunda, ella mateixa."""
    return SEPARADOR.join(categoria.split(SEPARADOR)[:nivell])


def sumar_per_node(imports, node=None):
    """
    Suma els imports {categoria: import} als fills de `node` (a l'arrel si és None), en l'ordre en
    què apareixen. El que és del node mateix (no de cap subcategoria) surt amb el nom del node.
    """
    nivell = len(node.split(SEPARADOR)) + 1 if node else 1
    resultat = {}
    for categoria, import_ in imports.items():
        if node and not es_dins(categoria, node):
            continue
        clau = categoria_a_nivell(categoria, nivell)
        resultat[clau] = resultat.get(clau, 0) + import_
    return resultat


def profunditat_maxima(noms):
    """Quants nivells té la categoria més profunda (0 si no n'hi ha cap)."""
    return max((len(nom.split(SEPARADOR)) for nom in noms), default=0)


def nodes_categories(noms):
    """
    Tots els nodes de l'arbre, també els intermedis que no tenen paraules clau pròpies. Els fills
    van just després del pare, en l'ordre en què apareixen per primer cop.
    """
    fills = {}  # node -> fills, en ordre d'aparició
    arrels = []
    for nom in noms:
        nivells = nom.split(SEPARADOR)
        for i in range(len(nivells)):
            node = SEPARADOR.join(nivells[:i + 1])
            germans = fills.setdefault(SEPARADOR.join(nivells[:i]), []) if i else arrels
            if node not in germans:
                germans.append(node)

    def recorrer(nodes):
        for node in nodes:
            yield node
            yield from recorrer(fills.get(node, []))

    return list(recorrer(arrels))


def parsejar_paraules_clau(text):
    """Converteix "a, b ,c" en ["a", "b", "c"], descartant els elements buits."""
    if not text:
        return []
    return [p.strip() for p in text.split(",") if p.strip()]
