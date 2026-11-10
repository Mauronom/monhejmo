from datetime import date
from decimal import Decimal
from domain import Moviment, PuntGrafica, calcular_punts


def _totals(punts):
    return [p for p in punts if p.banc == "Total"]


def test_saldo_zero_es_un_saldo_real():
    """Un banc que queda a 0 € ha de comptar com a 0, no com el saldo anterior."""
    moviments = [
        Moviment(date(2023, 1, 1), "Ingrés A", 100, 100, "A"),
        Moviment(date(2023, 1, 1), "Ingrés B", 50, 50, "B"),
        Moviment(date(2023, 1, 2), "Buidar A", -100, 0, "A"),
    ]

    totals = _totals(calcular_punts(moviments))

    assert totals[-1].saldo == 50  # A=0 + B=50, no 100 + 50


def test_ordre_dins_del_dia_per_banc():
    """Cada moviment té la seva posició dins del dia i el banc; no hi ha límit de moviments."""
    moviments = [Moviment(date(2023, 1, 1), f"Compra {i}", -1, 100 - i, "A") for i in range(30)]
    moviments += [Moviment(date(2023, 1, 1), "Altre banc", 5, 5, "B"),
                  Moviment(date(2023, 1, 2), "Endemà", -1, 69, "A")]

    punts = calcular_punts(moviments)

    del_banc_a = [p for p in punts if p.banc == "A"]
    assert [(p.data, p.ordre) for p in del_banc_a] == \
        [(date(2023, 1, 1), i) for i in range(30)] + [(date(2023, 1, 2), 0)]
    assert next(p for p in punts if p.banc == "B").ordre == 0


def test_un_total_per_instant_ordenat_per_data_ordre_i_banc():
    moviments = [
        Moviment(date(2023, 1, 1), "A1", 10, 10, "A"),
        Moviment(date(2023, 1, 1), "B1", 5, 5, "B"),
        Moviment(date(2023, 1, 1), "A2", 1, 11, "A"),
    ]

    punts = calcular_punts(moviments)

    assert [(p.ordre, p.banc, p.saldo, p.import_) for p in punts] == [
        (0, "A", 10, 10), (0, "B", 5, 5), (0, "Total", 15, 15),
        (1, "A", 11, 1), (1, "Total", 16, 1),
    ]


def test_els_saldos_son_decimal():
    moviments = [Moviment(date(2023, 1, 1), "X", "0.10", "0.30", "A"),
                 Moviment(date(2023, 1, 1), "Y", "0.20", "0.20", "B")]

    total = _totals(calcular_punts(moviments))[0]

    assert total.saldo == Decimal("0.50")
    assert isinstance(total.saldo, Decimal)


def test_els_punts_tenen_camps_amb_nom():
    moviments = [Moviment(date(2023, 1, 1), "Sou", 1000, 1000, "A")]

    punt = next(p for p in calcular_punts(moviments) if p.banc == "A")

    assert isinstance(punt, PuntGrafica)
    assert (punt.data, punt.ordre, punt.saldo, punt.concepte, punt.import_) == (date(2023, 1, 1), 0, 1000, "Sou", 1000)
