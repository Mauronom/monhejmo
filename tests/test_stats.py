from datetime import date
from decimal import Decimal
from domain import Moviment, Resum, calcular_stats


def test_calcular_stats_retorna_decimal_exacte():
    moviments = [
        Moviment(date(2023, 1, 1), "A", "0.10", 0, "B"),
        Moviment(date(2023, 1, 1), "B", "0.20", 0, "B"),
    ]

    resum = calcular_stats(moviments)

    assert isinstance(resum, Resum)
    assert resum.total == Decimal("0.30")
    assert isinstance(resum.diari, Decimal)
    assert isinstance(resum.mensual, Decimal)


def test_calcular_stats_no_modifica_la_llista():
    moviments = [
        Moviment(date(2023, 1, 2), "Segon", 1, 0, "B"),
        Moviment(date(2023, 1, 1), "Primer", 1, 0, "B"),
    ]

    calcular_stats(moviments)

    assert [m.concepte for m in moviments] == ["Segon", "Primer"]


def test_calcular_stats_sense_moviments_retorna_zeros():
    assert calcular_stats([]) == Resum(Decimal(0), Decimal(0), Decimal(0))
