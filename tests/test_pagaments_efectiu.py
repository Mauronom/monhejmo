from datetime import date
from decimal import Decimal
import pytest
from domain import (Moviment, PagamentEfectiu, SupositInvalid, validar_pagament_efectiu, generar_moviments_efectiu,
                    BANC_EFECTIU, CONCEPTE_EFECTIU_ASSIGNAT, calcular_stats)
from app import (CarregarMoviments, MovimentsSessio, LlistarPagamentsEfectiu, AfegirPagamentEfectiu,
                 EliminarPagamentEfectiu)
from infra import MemoryCategoriesRepo, MemoryRepositoriSuposits

NETEJA = PagamentEfectiu("Neteja", Decimal(200), "mensual", date(2025, 1, 15))


def test_cada_pagament_dona_la_despesa_i_la_part_de_l_efectiu_que_explica():
    moviments = generar_moviments_efectiu([NETEJA], date(2025, 3, 20))

    assert [(m.data, m.concepte, m.import_, m.balance, m.banc) for m in moviments] == [
        (date(2025, 1, 15), "Neteja (efectiu)", Decimal(-200), Decimal(0), BANC_EFECTIU),
        (date(2025, 1, 15), CONCEPTE_EFECTIU_ASSIGNAT, Decimal(200), Decimal(0), BANC_EFECTIU),
        (date(2025, 2, 15), "Neteja (efectiu)", Decimal(-200), Decimal(0), BANC_EFECTIU),
        (date(2025, 2, 15), CONCEPTE_EFECTIU_ASSIGNAT, Decimal(200), Decimal(0), BANC_EFECTIU),
        (date(2025, 3, 15), "Neteja (efectiu)", Decimal(-200), Decimal(0), BANC_EFECTIU),
        (date(2025, 3, 15), CONCEPTE_EFECTIU_ASSIGNAT, Decimal(200), Decimal(0), BANC_EFECTIU),
    ]
    assert sum(m.import_ for m in moviments) == 0  # el total no canvia


def test_respecta_la_data_de_fi_del_pagament():
    classes = PagamentEfectiu("Classes", Decimal(50), "trimestral", date(2025, 1, 10), data_fi=date(2025, 6, 30))

    moviments = generar_moviments_efectiu([classes], date(2026, 1, 1))

    assert sorted({m.data for m in moviments}) == [date(2025, 1, 10), date(2025, 4, 10)]


def test_els_pagaments_que_comencen_despres_de_les_dades_no_hi_son():
    assert generar_moviments_efectiu([NETEJA], date(2025, 1, 1)) == []


@pytest.mark.parametrize("pagament", [
    PagamentEfectiu(" ", Decimal(200), "mensual", date(2025, 1, 15)),
    PagamentEfectiu("Neteja", Decimal(-200), "mensual", date(2025, 1, 15)),
    PagamentEfectiu("Neteja", Decimal(0), "mensual", date(2025, 1, 15)),
    PagamentEfectiu("Neteja", Decimal(200), "quinzenal", date(2025, 1, 15)),
    PagamentEfectiu("Neteja", Decimal(200), "mensual", date(2025, 1, 15), data_fi=date(2025, 1, 1)),
])
def test_pagaments_invalids(pagament):
    with pytest.raises(SupositInvalid):
        validar_pagament_efectiu(pagament)


# --- Càrrega -------------------------------------------------------------------------------

class FontFalsa:
    def llegir(self, directori):
        return [Moviment(date(2025, 1, 2), "CAJERO", -300, 700, "banc"),
                Moviment(date(2025, 2, 28), "NOMINA", 2000, 2700, "banc")]


CATEGORIES = {"efectiu": ["cajero", "retirada efectivo"], "neteja_casa": ["neteja"]}


def _carregar(pagaments):
    sessio = MovimentsSessio()
    cas_us = CarregarMoviments(FontFalsa(), None, MemoryCategoriesRepo(dict(CATEGORIES)), sessio,
                               MemoryRepositoriSuposits(pagaments))
    return cas_us.execute("/dades")


def test_la_carrega_afegeix_els_pagaments_en_efectiu_fins_al_darrer_moviment():
    resultat = _carregar([NETEJA])

    efectiu = [m for m in resultat.moviments if m.banc == BANC_EFECTIU]
    assert [(m.data, m.categoria, m.import_) for m in efectiu] == [
        (date(2025, 1, 15), "neteja_casa", Decimal(-200)), (date(2025, 1, 15), "efectiu", Decimal(200)),
        (date(2025, 2, 15), "neteja_casa", Decimal(-200)), (date(2025, 2, 15), "efectiu", Decimal(200)),
    ]
    assert resultat.resum.total == calcular_stats(FontFalsa().llegir("")).total


def test_la_carrega_sense_repositori_de_pagaments_funciona_com_abans():
    sessio = MovimentsSessio()
    resultat = CarregarMoviments(FontFalsa(), None, MemoryCategoriesRepo(dict(CATEGORIES)), sessio).execute("/d")

    assert BANC_EFECTIU not in {m.banc for m in resultat.moviments}


# --- Casos d'ús i JSON ---------------------------------------------------------------------

def test_afegir_llistar_i_eliminar_pagaments():
    repo = MemoryRepositoriSuposits()

    AfegirPagamentEfectiu(repo).execute(NETEJA)
    assert LlistarPagamentsEfectiu(repo).execute() == [NETEJA]
    with pytest.raises(SupositInvalid):
        AfegirPagamentEfectiu(repo).execute(PagamentEfectiu("", Decimal(1), "mensual", date(2025, 1, 1)))
    assert EliminarPagamentEfectiu(repo).execute(0)
    assert LlistarPagamentsEfectiu(repo).execute() == []


def test_json_desa_els_pagaments_a_la_seva_seccio(tmp_path):
    import json
    from infra import JsonRepositoriPagamentsEfectiu
    fitxer = tmp_path / "config.json"
    fitxer.write_text(json.dumps({"previsio": {"horitzo_mesos": 12}}), encoding="utf-8")

    JsonRepositoriPagamentsEfectiu(fitxer).save_all([NETEJA])

    config = json.loads(fitxer.read_text(encoding="utf-8"))
    assert config["pagaments_efectiu"] == [
        {"concepte": "Neteja", "import": "200", "periodicitat": "mensual", "inici": "2025-01-15", "fi": None}]
    assert config["previsio"] == {"horitzo_mesos": 12}
    assert JsonRepositoriPagamentsEfectiu(fitxer).get_all() == [NETEJA]


def test_un_pagament_setmanal_es_fa_cada_set_dies():
    neteja = PagamentEfectiu("Neteja", Decimal(40), "setmanal", date(2025, 1, 2))

    moviments = generar_moviments_efectiu([neteja], date(2025, 1, 31))

    assert sorted({m.data for m in moviments}) == [date(2025, 1, 2), date(2025, 1, 9), date(2025, 1, 16),
                                                   date(2025, 1, 23), date(2025, 1, 30)]
    validar_pagament_efectiu(neteja)
