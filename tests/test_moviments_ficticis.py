from datetime import date
from domain import Moviment, ReglaMovimentFictici, generar_moviments_ficticis

ORIGINALS = [
    Moviment(date(2025, 1, 1), "Sou", 2000, 5000, "Banc A"),
    Moviment(date(2025, 1, 2), "Compra supermercat", -50, 4950, "Banc A"),
    Moviment(date(2025, 1, 3), "PLAN AHORRO 5 SIALP", -100, 4850, "Banc B"),
    Moviment(date(2025, 1, 5), "CI PIAS", -100, 4750, "Banc B"),
]
REGLA_SIALP = ReglaMovimentFictici(
    patrons=["PLAN AHORRO 5 SIALP", "CI PIAS"], concepte_desti="SIALP PIES", banc_desti="SIALP_PIAS")
INICIAL_SIALP = Moviment(date(2024, 8, 1), "SIALP PIES", 0, 10000, "SIALP_PIAS")


def test_sense_regles_ni_inicials_no_genera_res():
    assert generar_moviments_ficticis(ORIGINALS, [], []) == []


def test_nomes_inicials():
    ficticis = generar_moviments_ficticis(ORIGINALS, [], [INICIAL_SIALP])

    assert ficticis == [INICIAL_SIALP]
    assert ficticis[0] is not INICIAL_SIALP  # és una còpia


def test_regla_genera_un_moviment_per_coincidencia_amb_import_invertit_i_saldo_acumulat():
    ficticis = generar_moviments_ficticis(ORIGINALS, [REGLA_SIALP], [INICIAL_SIALP])

    assert [(m.data, m.concepte, m.import_, m.balance, m.banc) for m in ficticis] == [
        (date(2024, 8, 1), "SIALP PIES", 0, 10000, "SIALP_PIAS"),
        (date(2025, 1, 3), "SIALP PIES", 100, 10100, "SIALP_PIAS"),
        (date(2025, 1, 5), "SIALP PIES", 100, 10200, "SIALP_PIAS"),
    ]


def test_sense_invertir_import():
    regla = ReglaMovimentFictici(patrons=["CI PIAS"], concepte_desti="X", banc_desti="X", invertir_import=False)

    ficticis = generar_moviments_ficticis(ORIGINALS, [regla], [])

    assert ficticis[0].import_ == -100


def test_nomes_s_aplica_la_primera_regla_que_coincideix():
    primera = ReglaMovimentFictici(patrons=["CI PIAS"], concepte_desti="Primera", banc_desti="P")
    segona = ReglaMovimentFictici(patrons=["PIAS"], concepte_desti="Segona", banc_desti="S")

    ficticis = generar_moviments_ficticis(ORIGINALS, [primera, segona], [])

    assert [m.concepte for m in ficticis] == ["Primera"]


def test_els_patrons_distingeixen_majuscules():
    regla = ReglaMovimentFictici(patrons=["ci pias"], concepte_desti="X", banc_desti="X")

    assert generar_moviments_ficticis(ORIGINALS, [regla], []) == []


def test_saldo_per_banc_desti():
    regla_sialp = ReglaMovimentFictici(patrons=["PLAN AHORRO 5 SIALP"], concepte_desti="SIALP", banc_desti="SIALP")
    regla_pias = ReglaMovimentFictici(patrons=["CI PIAS"], concepte_desti="PIAS", banc_desti="PIAS")
    inicials = [
        Moviment(date(2024, 7, 1), "Inicial SIALP", 0, 1000, "SIALP"),
        Moviment(date(2024, 7, 1), "Inicial PIAS", 0, 500, "PIAS"),
    ]

    ficticis = generar_moviments_ficticis(ORIGINALS, [regla_sialp, regla_pias], inicials)

    saldos = {m.concepte: m.balance for m in ficticis}
    assert saldos["SIALP"] == 1100
    assert saldos["PIAS"] == 600


def test_banc_desti_sense_inicial_parteix_de_zero():
    regla = ReglaMovimentFictici(patrons=["CI PIAS"], concepte_desti="PIAS", banc_desti="PIAS")
    inicials = [Moviment(date(2024, 7, 1), "Inicial altre", 0, 1000, "ALTRE")]

    ficticis = generar_moviments_ficticis(ORIGINALS, [regla], inicials)

    assert ficticis[-1].balance == 100


def test_no_modifica_els_originals():
    abans = [m.clone() for m in ORIGINALS]

    generar_moviments_ficticis(ORIGINALS, [REGLA_SIALP], [INICIAL_SIALP])

    assert ORIGINALS == abans
