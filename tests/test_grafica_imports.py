import pytest
from datetime import date
from domain import Moviment, FiltreMoviments
from app import GraficaImports, MovimentsSessio

MOVIMENTS = [
    Moviment(data=date(2023, 1, 1), concepte="Sou", import_=1000, balance=1000, banc="TestBank"),
    Moviment(data=date(2023, 1, 1), concepte="Compra matí", import_=-100, balance=900, banc="TestBank"),
    Moviment(data=date(2023, 1, 1), concepte="Alt banc", import_=200, balance=200, banc="OtherBank"),
    Moviment(data=date(2023, 1, 2), concepte="Lloguer", import_=-500, balance=350, banc="TestBank"),
]


def _sessio(moviments):
    sessio = MovimentsSessio()
    sessio.substituir(moviments)
    return sessio


def test_mostrar_grafica_converteix_moviments_a_punts_amb_banc():
    resultat = GraficaImports(_sessio(MOVIMENTS)).execute(FiltreMoviments())

    dades = resultat
    # Punts: data, ordre dins del dia, saldo, banc, concepte, import
    esperats = [
        (date(2023, 1, 1), 0, 200, "OtherBank", "Alt banc", 200),
        (date(2023, 1, 1), 0, 1000, "TestBank", "Sou", 1000),
        (date(2023, 1, 1), 0, 1200, "Total", "Total", 1200),
        (date(2023, 1, 1), 1, 900, "TestBank", "Compra matí", -100),
        (date(2023, 1, 1), 1, 1100, "Total", "Total", -100),
        (date(2023, 1, 2), 0, 400, "TestBank", "Lloguer", -500),
        (date(2023, 1, 2), 0, 600, "Total", "Total", -500),
    ]
    assert dades["punts"] == esperats

    # Els eixos han de ser coherents
    assert dades["etiqueta_x"] == "Data/Hora"
    assert dades["etiqueta_y"] == "Import Acumulat"

    