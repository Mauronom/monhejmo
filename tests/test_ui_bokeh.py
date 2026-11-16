from datetime import date, datetime, timedelta
import pytest
from domain import Moviment, calcular_punts
from infra.ui_bokeh import hores_dels_punts


def test_fins_a_24_per_dia_una_hora_per_posicio():
    punts = calcular_punts([
        Moviment(date(2023, 1, 1), "A1", 1, 1, "A"),
        Moviment(date(2023, 1, 1), "A2", 1, 2, "A"),
        Moviment(date(2023, 1, 1), "B1", 1, 1, "B"),
        Moviment(date(2023, 1, 2), "A3", 1, 3, "A"),
    ])

    hores = dict(zip([(p.concepte, p.banc) for p in punts], hores_dels_punts(punts)))

    assert hores[("A1", "A")] == datetime(2023, 1, 1, 0)
    assert hores[("A2", "A")] == datetime(2023, 1, 1, 1)
    assert hores[("B1", "B")] == datetime(2023, 1, 1, 0)
    assert hores[("A3", "A")] == datetime(2023, 1, 2, 0)


def test_mes_de_24_es_reparteixen_dins_del_dia_en_ordre():
    moviments = [Moviment(date(2023, 1, 1), f"Compra {i}", -1, 100 - i, "A") for i in range(30)]
    moviments.append(Moviment(date(2023, 1, 2), "Endemà", -1, 69, "A"))
    punts = calcular_punts(moviments)

    hores = [h for p, h in zip(punts, hores_dels_punts(punts)) if p.banc == "A"]

    del_dia_1 = hores[:-1]
    assert all(h.date() == date(2023, 1, 1) for h in del_dia_1)
    assert del_dia_1 == sorted(set(del_dia_1))
    assert del_dia_1[1] - del_dia_1[0] == timedelta(days=1) / 30
    assert hores[-1] == datetime(2023, 1, 2)


def test_el_total_va_a_la_mateixa_hora_que_els_moviments_del_seu_instant():
    punts = calcular_punts([Moviment(date(2023, 1, 1), "A1", 1, 1, "A"), Moviment(date(2023, 1, 1), "A2", 1, 2, "A")])

    hores = {(p.banc, p.ordre): h for p, h in zip(punts, hores_dels_punts(punts))}

    assert hores[("Total", 1)] == hores[("A", 1)] == datetime(2023, 1, 1, 1)


def test_inicis_de_mes_entre_dues_dates():
    from infra.ui_bokeh import inicis_de_mes_entre

    # Des del dia 1 del mes de la primera data fins a la darrera, passant de desembre a gener
    assert inicis_de_mes_entre(date(2025, 11, 20), date(2026, 2, 1)) == [
        date(2025, 11, 1), date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)]
    assert inicis_de_mes_entre(date(2026, 3, 1), date(2026, 3, 31)) == [date(2026, 3, 1)]


def test_desglossos_de_categories_per_a_cada_node_amb_subcategories():
    from infra.ui_bokeh import desglossos_categories
    imports = {"casa/llum": -50.0, "oci": -10.0, "casa/aigua": -30.0, "menjar/super/carn": -20.0}

    assert desglossos_categories(imports) == {
        "": {"casa": -80.0, "oci": -10.0, "menjar": -20.0},
        "casa": {"casa/llum": -50.0, "casa/aigua": -30.0},
        "menjar": {"menjar/super": -20.0},
        "menjar/super": {"menjar/super/carn": -20.0},
    }


def test_columnes_pastis():
    from infra.ui_bokeh import columnes_pastis
    import math
    columnes = columnes_pastis({"casa": -75.0, "oci": -25.0})

    assert columnes["categoria"] == ["casa", "oci"]
    assert columnes["quantitat"] == [75.0, 25.0]
    assert columnes["percentatge"] == [75.0, 25.0]
    assert columnes["angle_start"] == pytest.approx([0, 1.5 * math.pi])
    assert columnes["angle_end"] == pytest.approx([1.5 * math.pi, 2 * math.pi])
    assert len(columnes["color"]) == 2


def test_columnes_pastis_buit():
    from infra.ui_bokeh import columnes_pastis
    assert columnes_pastis({})["categoria"] == []
