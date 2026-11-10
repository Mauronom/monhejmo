from datetime import date
from domain import Moviment, CATEGORIA_PER_DEFECTE, assignar_categories_a_moviments
from infra import MemoryCategoriesRepo


def test_un_moviment_nou_te_la_categoria_per_defecte():
    assert Moviment(date(2023, 1, 1), "X", 1, 1, "A").categoria == CATEGORIA_PER_DEFECTE


def test_sense_coincidencies_s_assigna_la_categoria_per_defecte():
    moviments = [Moviment(date(2023, 1, 1), "Res a veure", 1, 1, "A", "oci")]

    resultat = assignar_categories_a_moviments(moviments, MemoryCategoriesRepo({"casa": ["lloguer"]}))

    assert resultat[0].categoria == CATEGORIA_PER_DEFECTE
