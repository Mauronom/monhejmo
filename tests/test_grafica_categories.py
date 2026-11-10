import pytest
from datetime import date, datetime
from domain import Moviment, FiltreMoviments
from app import GraficaCategories, MovimentsSessio

MOVIMENTS = [
    Moviment(data=date(2023, 1, 1), concepte="Sou", import_=1000, balance=1000, banc="TestBank",categoria="nomina"),
    Moviment(data=date(2023, 1, 1), concepte="Compra matí", import_=-100, balance=900, banc="TestBank",categoria="alimentació"),
    Moviment(data=date(2023, 1, 1), concepte="Alt banc", import_=200, balance=200, banc="OtherBank",categoria="habitatge"),
    Moviment(data=date(2023, 1, 2), concepte="Lloguer", import_=-500, balance=350, banc="TestBank", categoria="habitatge"),
]


def _sessio(moviments):
    sessio = MovimentsSessio()
    sessio.substituir(moviments)
    return sessio


def test_mostrar_grafica_converteix_moviments_despeses_per_categoria():
    resultat = GraficaCategories(_sessio(MOVIMENTS)).execute(FiltreMoviments())

    assert resultat == {'alimentació': -100.0, 'habitatge': -300.0}

    

def test_les_grafiques_nomes_fan_servir_els_moviments_filtrats():
    resultat = GraficaCategories(_sessio(MOVIMENTS)).execute(FiltreMoviments(data_fi=date(2023, 1, 1)))

    # Sense el lloguer del dia 2, "habitatge" no té despeses i no surt
    assert resultat == {'alimentació': -100.0}
