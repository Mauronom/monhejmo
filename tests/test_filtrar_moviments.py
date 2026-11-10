from datetime import date
from decimal import Decimal
from domain import Moviment, FiltreMoviments, filtrar_moviments
from app import FiltrarMoviments, MovimentsSessio

MOVIMENTS = [
    Moviment(date(2023, 2, 15), "Gasolina", 40, -470, "BancB"),
    Moviment(date(2023, 1, 1), "Neteja", 50, 100, "BancA"),
    Moviment(date(2023, 1, 15), "Supermercat", 30, 70, "BancA", categoria="alimentació"),
    Moviment(date(2023, 2, 1), "Lloguer", 500, -430, "BancB"),
    Moviment(date(2023, 1, 5), "SUPERMERCAT Bonpreu", 25, 75, "BancA"),
]


def _conceptes(moviments):
    return [m.concepte for m in moviments]


# --- filtrar_moviments (domini)

def test_sense_filtre_retorna_tots_ordenats_per_data():
    resultat = filtrar_moviments(MOVIMENTS, FiltreMoviments())

    assert [m.data for m in resultat] == sorted(m.data for m in MOVIMENTS)


def test_filtre_de_text_no_distingeix_majuscules():
    resultat = filtrar_moviments(MOVIMENTS, FiltreMoviments(text="super"))

    assert _conceptes(resultat) == ["SUPERMERCAT Bonpreu", "Supermercat"]


def test_filtre_per_categoria():
    resultat = filtrar_moviments(MOVIMENTS, FiltreMoviments(text="super", categoria="alimentació"))

    assert _conceptes(resultat) == ["Supermercat"]


def test_filtre_per_data_inici():
    resultat = filtrar_moviments(MOVIMENTS, FiltreMoviments(data_inici=date(2023, 1, 10)))

    assert _conceptes(resultat) == ["Supermercat", "Lloguer", "Gasolina"]


def test_filtre_per_data_fi():
    resultat = filtrar_moviments(MOVIMENTS, FiltreMoviments(data_fi=date(2023, 1, 15)))

    assert _conceptes(resultat) == ["Neteja", "SUPERMERCAT Bonpreu", "Supermercat"]


def test_filtre_per_rang_de_dates_inclou_els_extrems():
    resultat = filtrar_moviments(MOVIMENTS, FiltreMoviments(data_inici=date(2023, 1, 15), data_fi=date(2023, 2, 1)))

    assert _conceptes(resultat) == ["Supermercat", "Lloguer"]


def test_data_inici_posterior_a_data_fi_no_retorna_res():
    assert filtrar_moviments(MOVIMENTS, FiltreMoviments(data_inici=date(2023, 1, 20), data_fi=date(2023, 1, 10))) == []


def test_mateix_dia_ordena_per_banc():
    moviments = [Moviment(date(2023, 1, 1), "X", 1, 1, "Z"), Moviment(date(2023, 1, 1), "Y", 1, 1, "A")]

    assert [m.banc for m in filtrar_moviments(moviments, FiltreMoviments())] == ["A", "Z"]


# --- FiltrarMoviments (cas d'ús): filtra la sessió i calcula el resum del període

def _sessio():
    sessio = MovimentsSessio()
    sessio.substituir(MOVIMENTS)
    return sessio


def test_cas_us_sense_filtre():
    resultat = FiltrarMoviments(_sessio()).execute(FiltreMoviments())

    assert len(resultat.moviments) == 5
    assert resultat.resum.total == Decimal("645")
    assert resultat.resum.diari == Decimal("645") / 46  # de l'1/1 al 15/2


def test_cas_us_el_periode_del_resum_inclou_les_dates_del_filtre():
    filtre = FiltreMoviments(data_inici=date(2023, 1, 10), data_fi=date(2023, 2, 5))

    resultat = FiltrarMoviments(_sessio()).execute(filtre)

    assert resultat.resum.total == Decimal("530")
    assert resultat.resum.diari == Decimal("530") / 27
    assert resultat.resum.mensual == Decimal("530") / 27 * 30


def test_cas_us_sense_resultats():
    resultat = FiltrarMoviments(_sessio()).execute(FiltreMoviments(text="no hi és"))

    assert resultat.moviments == []
    assert resultat.resum.total == 0
