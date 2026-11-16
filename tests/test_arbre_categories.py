from datetime import date
from decimal import Decimal
import pytest
from domain import (Moviment, FiltreMoviments, filtrar_moviments, CategoriaInvalida, validar_nom_categoria,
                    es_dins, es_dins_algun, categoria_a_nivell, nodes_categories, CriterisDespesesVariables,
                    calcular_despeses_variables, ConfigPrevisio, resta_mensual)


@pytest.mark.parametrize("categoria, node, esperat", [
    ("casa/subministraments/llum", "casa", True),
    ("casa/subministraments/llum", "casa/subministraments", True),
    ("casa/subministraments/llum", "casa/subministraments/llum", True),
    ("casa", "casa", True),
    ("casament", "casa", False),  # no n'hi ha prou que comenci igual
    ("casa", "casa/subministraments", False),  # el pare no és dins del fill
    ("oci", "casa", False),
])
def test_es_dins(categoria, node, esperat):
    assert es_dins(categoria, node) == esperat


def test_es_dins_algun():
    assert es_dins_algun("casa/llum", ("oci", "casa"))
    assert not es_dins_algun("casa/llum", ("oci",))
    assert not es_dins_algun("casa/llum", ())


@pytest.mark.parametrize("nivell, esperat", [
    (1, "casa"), (2, "casa/subministraments"), (3, "casa/subministraments/llum"), (9, "casa/subministraments/llum")])
def test_categoria_a_nivell(nivell, esperat):
    assert categoria_a_nivell("casa/subministraments/llum", nivell) == esperat


def test_nodes_categories_inclou_els_intermedis_i_cada_pare_va_davant_dels_fills():
    noms = ["oci", "casa/subministraments/llum", "casa/habitatge", "casa/subministraments/gas", "casa"]

    assert nodes_categories(noms) == ["oci", "casa", "casa/subministraments", "casa/subministraments/llum",
                                      "casa/subministraments/gas", "casa/habitatge"]


@pytest.mark.parametrize("nom", ["casa/", "/casa", "casa//llum", "casa/ /llum"])
def test_no_es_pot_desar_una_categoria_amb_un_nivell_buit(nom):
    with pytest.raises(CategoriaInvalida):
        validar_nom_categoria(nom)


def test_es_pot_desar_una_categoria_amb_nivells():
    validar_nom_categoria("casa/subministraments/llum")


# --- On es fan servir -------------------------------------------------------

def _mov(dia, import_, categoria):
    return Moviment(date(2025, 1, dia), f"MOVIMENT {dia}", Decimal(import_), 0, "banc", categoria)


LLUM, GAS, LLOGUER, CINEMA = (_mov(1, -50, "casa/subministraments/llum"), _mov(2, -30, "casa/subministraments/gas"),
                              _mov(3, -700, "casa/habitatge"), _mov(4, -10, "oci"))
MOVIMENTS = [LLUM, GAS, LLOGUER, CINEMA]


def test_filtrar_per_un_node_inclou_tots_els_seus_descendents():
    assert filtrar_moviments(MOVIMENTS, FiltreMoviments(categoria="casa")) == [LLUM, GAS, LLOGUER]
    assert filtrar_moviments(MOVIMENTS, FiltreMoviments(categoria="casa/subministraments")) == [LLUM, GAS]
    assert filtrar_moviments(MOVIMENTS, FiltreMoviments(categoria="casa/subministraments/llum")) == [LLUM]


def test_excloure_un_node_a_les_despeses_variables_exclou_els_descendents():
    criteris = CriterisDespesesVariables(categories_excloses=("casa/subministraments",))

    resultat = calcular_despeses_variables(MOVIMENTS, [], criteris)

    assert [c.categoria for c in resultat.per_categoria] == ["casa/habitatge", "oci"]


def test_excloure_un_node_a_la_previsio_exclou_els_descendents():
    from domain import preveure, CriterisRecurrents
    # Un moviment del febrer perquè el gener sigui un mes complet de l'històric
    moviments = MOVIMENTS + [Moviment(date(2025, 2, 28), "FEBRER", Decimal(0), 0, "banc", "oci")]

    previsio = preveure(moviments, CriterisRecurrents(), CriterisRecurrents(),
                        ConfigPrevisio(mesos_historic=1, categories_excloses=("casa",)))

    assert previsio.variable_mensual == Decimal(-10)  # només el cinema


def test_les_despeses_variables_es_poden_agrupar_a_un_nivell():
    resultat = calcular_despeses_variables(MOVIMENTS, [], CriterisDespesesVariables(), nivell=1)

    assert [(c.categoria, c.total, c.moviments) for c in resultat.per_categoria] == [
        ("casa", Decimal(780), 3), ("oci", Decimal(10), 1)]
    assert resultat.total == Decimal(790)


def test_agrupar_a_un_nivell_mes_profund_que_una_categoria_la_deixa_tal_com_es():
    resultat = calcular_despeses_variables(MOVIMENTS, [], CriterisDespesesVariables(), nivell=2)

    assert [(c.categoria, c.total) for c in resultat.per_categoria] == [
        ("casa/habitatge", Decimal(700)), ("casa/subministraments", Decimal(80)), ("oci", Decimal(10))]


def test_sense_nivell_les_despeses_variables_van_a_la_categoria_mes_concreta():
    resultat = calcular_despeses_variables(MOVIMENTS, [], CriterisDespesesVariables())

    assert [c.categoria for c in resultat.per_categoria] == [
        "casa/habitatge", "casa/subministraments/llum", "casa/subministraments/gas", "oci"]


def test_profunditat_maxima():
    from domain import profunditat_maxima
    assert profunditat_maxima(["oci", "casa/subministraments/llum", "casa/habitatge"]) == 3
    assert profunditat_maxima([]) == 0


# --- Desglòs per nodes (gràfica de categories) --------------------------------

IMPORTS = {"casa/subministraments/llum": -50.0, "oci": -10.0, "casa/habitatge": -700.0,
           "casa/subministraments/gas": -30.0, "casa": -5.0}


def test_sumar_per_node_a_l_arrel_agrupa_al_primer_nivell_en_ordre_d_aparicio():
    from domain import sumar_per_node
    assert sumar_per_node(IMPORTS) == {"casa": -785.0, "oci": -10.0}


def test_sumar_per_node_dona_els_fills_d_un_node_i_el_que_es_del_node_mateix():
    from domain import sumar_per_node
    assert sumar_per_node(IMPORTS, "casa") == {"casa/subministraments": -80.0, "casa/habitatge": -700.0,
                                               "casa": -5.0}
    assert sumar_per_node(IMPORTS, "casa/subministraments") == {"casa/subministraments/llum": -50.0,
                                                                "casa/subministraments/gas": -30.0}


def test_sumar_per_node_d_una_fulla_no_dona_res():
    from domain import sumar_per_node
    assert sumar_per_node(IMPORTS, "oci") == {"oci": -10.0}
    assert sumar_per_node(IMPORTS, "casa/habitatge") == {"casa/habitatge": -700.0}
