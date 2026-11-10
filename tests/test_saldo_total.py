from datetime import date
from decimal import Decimal
from domain import Moviment, FiltreMoviments, saldos_totals
from app import FiltrarMoviments, MovimentsSessio, CarregarMoviments
from infra import MemoryCategoriesRepo

MOVIMENTS = [
    Moviment(date(2025, 1, 1), "Sou", 1000, 1000, "A"),
    Moviment(date(2025, 1, 2), "Super", -100, 400, "B"),
    Moviment(date(2025, 1, 3), "Lloguer", -500, 500, "A"),
    Moviment(date(2025, 1, 3), "Super", -50, 350, "B"),
]


def test_cada_moviment_te_la_suma_del_darrer_saldo_de_cada_banc():
    assert saldos_totals(MOVIMENTS) == [Decimal(1000), Decimal(1400), Decimal(900), Decimal(850)]


def test_el_resultat_va_en_l_ordre_dels_moviments_que_es_passen():
    assert saldos_totals(list(reversed(MOVIMENTS))) == [Decimal(850), Decimal(900), Decimal(1400), Decimal(1000)]


def test_filtrar_dona_el_saldo_total_de_tots_els_bancs_encara_que_es_filtri():
    sessio = MovimentsSessio()
    sessio.substituir(MOVIMENTS)

    resultat = FiltrarMoviments(sessio).execute(FiltreMoviments(text="super"))

    assert [m.concepte for m in resultat.moviments] == ["Super", "Super"]
    assert resultat.saldos_totals == [Decimal(1400), Decimal(850)]


def test_carregar_tambe_dona_els_saldos_totals():
    class Font:
        def llegir(self, directori):
            return [m.clone() for m in MOVIMENTS]

    resultat = CarregarMoviments(Font(), None, MemoryCategoriesRepo({}), MovimentsSessio()).execute("/d")

    assert resultat.saldos_totals == [Decimal(1000), Decimal(1400), Decimal(900), Decimal(850)]
