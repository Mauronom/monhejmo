from datetime import date
from decimal import Decimal
from domain import (Moviment, CriterisDespesesVariables, calcular_despeses_variables, detectar_recurrents,
                    CriterisRecurrents, CONCEPTE_EFECTIU_ASSIGNAT, CATEGORIA_TRASPAS)


def _mov(data, concepte, import_, categoria, banc="banc"):
    return Moviment(data=data, concepte=concepte, import_=Decimal(import_), balance=0, banc=banc,
                    categoria=categoria)


SUPER_GENER = _mov(date(2025, 1, 10), "SUPERMERCAT", "-80", "alimentacio")
SUPER_MARC = _mov(date(2025, 3, 20), "SUPERMERCAT", "-120", "alimentacio")
CINEMA = _mov(date(2025, 2, 14), "CINEMA", "-30", "oci")
NOMINA = _mov(date(2025, 1, 28), "NOMINA", "2000", "nomina")
SOFA = _mov(date(2025, 2, 3), "BOTIGA DE MOBLES", "-1500", "compra")


def _calcular(moviments, recurrents=(), criteris=CriterisDespesesVariables(), **dates):
    return calcular_despeses_variables(moviments, recurrents, criteris, **dates)


def test_suma_les_despeses_per_categoria_de_mes_a_menys():
    resultat = _calcular([SUPER_GENER, CINEMA, SUPER_MARC])

    assert [(c.categoria, c.total, c.moviments) for c in resultat.per_categoria] == [
        ("alimentacio", Decimal(200), 2), ("oci", Decimal(30), 1)]
    assert resultat.total == Decimal(230)


def test_la_mitjana_mensual_es_el_total_repartit_pels_mesos_del_periode():
    # De l'1 de gener al 31 de desembre: 365 dies, uns 12 mesos
    resultat = _calcular([SUPER_GENER, CINEMA, SUPER_MARC],
                         data_inici=date(2025, 1, 1), data_fi=date(2025, 12, 31))

    assert resultat.mesos == Decimal("11.99")
    assert resultat.mensual == Decimal("19.18")
    assert resultat.per_categoria[0].mensual == Decimal("16.68")


def test_sense_dates_el_periode_va_del_primer_al_darrer_moviment():
    resultat = _calcular([SUPER_GENER, SUPER_MARC])  # del 10 de gener al 20 de març: 70 dies

    assert resultat.mesos == Decimal("2.30")


def test_no_compta_els_ingressos_ni_els_traspassos():
    traspas = _mov(date(2025, 1, 5), "TRANSF A COMPTE PROPI", "-500", CATEGORIA_TRASPAS)

    resultat = _calcular([SUPER_GENER, NOMINA, traspas])

    assert [c.categoria for c in resultat.per_categoria] == ["alimentacio"]


def test_no_compta_les_categories_excloses():
    estalvi = _mov(date(2025, 1, 5), "PLA D'ESTALVI", "-100", "estalvi")

    resultat = _calcular([SUPER_GENER, estalvi], criteris=CriterisDespesesVariables(categories_excloses=("estalvi",)))

    assert [c.categoria for c in resultat.per_categoria] == ["alimentacio"]


def test_no_compta_les_despeses_fixes():
    mutua = [_mov(date(2025, m, 2), "R/ MUTUA", "-60", "salut") for m in range(1, 6)]
    farmacia = _mov(date(2025, 2, 9), "FARMACIA", "-15", "salut")
    moviments = mutua + [farmacia]

    resultat = _calcular(moviments, detectar_recurrents(moviments, CriterisRecurrents()))

    assert [(c.categoria, c.total) for c in resultat.per_categoria] == [("salut", Decimal(15))]


def test_les_despeses_grosses_van_a_part_de_la_grossa_a_la_petita():
    nevera = _mov(date(2025, 3, 1), "ELECTRODOMESTICS", "-1000.01", "compra")
    llibre = _mov(date(2025, 3, 2), "LLIBRERIA", "-1000", "compra")  # just al llindar, no és grossa

    resultat = _calcular([SUPER_GENER, SOFA, nevera, llibre])

    assert resultat.puntuals == [SOFA, nevera]
    assert resultat.total_puntuals == Decimal("2500.01")
    assert [(c.categoria, c.total) for c in resultat.per_categoria] == [
        ("compra", Decimal(1000)), ("alimentacio", Decimal(80))]
    assert resultat.total == Decimal(1080)


def test_el_llindar_de_les_puntuals_es_configurable():
    resultat = _calcular([SUPER_GENER, SOFA], criteris=CriterisDespesesVariables(llindar_puntual=Decimal(50)))

    assert resultat.puntuals == [SOFA, SUPER_GENER]
    assert resultat.per_categoria == []


def test_la_part_assignada_de_les_retirades_d_efectiu_no_compta():
    # Una retirada de 200 €, dels quals 150 són un pagament fix en efectiu
    retirada = _mov(date(2025, 1, 4), "RETIRADA EFECTIVO", "-200", "efectiu")
    assignada = _mov(date(2025, 1, 4), CONCEPTE_EFECTIU_ASSIGNAT, "150", "efectiu", banc="EFECTIU")

    resultat = _calcular([retirada, assignada])

    assert [(c.categoria, c.total, c.moviments) for c in resultat.per_categoria] == [("efectiu", Decimal(50), 1)]


def test_una_categoria_sense_despesa_neta_no_surt():
    retirada = _mov(date(2025, 1, 4), "RETIRADA EFECTIVO", "-100", "efectiu")
    assignada = _mov(date(2025, 1, 4), CONCEPTE_EFECTIU_ASSIGNAT, "100", "efectiu", banc="EFECTIU")

    resultat = _calcular([SUPER_GENER, retirada, assignada])

    assert [c.categoria for c in resultat.per_categoria] == ["alimentacio"]


def test_sense_moviments_tot_es_zero():
    resultat = _calcular([])

    assert resultat.per_categoria == []
    assert resultat.puntuals == []
    assert resultat.total == resultat.mensual == resultat.total_puntuals == Decimal(0)
