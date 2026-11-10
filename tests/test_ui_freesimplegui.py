from datetime import date
import pytest
from infra.ui_freesimplegui import llegir_data, construir_filtre


@pytest.mark.parametrize("text, esperat", [
    ("2023-01-15", date(2023, 1, 15)),
    ("  2023-01-15 ", date(2023, 1, 15)),
    ("", None),
    (None, None),
    ("15/01/2023", None),
    ("2023-02-30", None),
])
def test_llegir_data(text, esperat):
    assert llegir_data(text) == esperat


def test_construir_filtre_totes_vol_dir_sense_categoria():
    filtre = construir_filtre("super", "2023-01-01", "data dolenta", "Totes")

    assert filtre.text == "super"
    assert filtre.data_inici == date(2023, 1, 1)
    assert filtre.data_fi is None
    assert filtre.categoria is None


def test_construir_filtre_amb_categoria():
    assert construir_filtre("", "", "", "oci").categoria == "oci"


def test_files_recurrents():
    from decimal import Decimal
    from domain import MovimentRecurrent
    from infra.ui_freesimplegui import files_recurrents

    despesa = MovimentRecurrent(concepte="R/ MUTUA", banc="caixa", categoria="salut", carrecs=12,
                          import_habitual=Decimal("117.5"), import_mensual=Decimal("118.43"),
                          periodicitat="mensual", primera=date(2025, 1, 5), darrera=date(2025, 12, 5),
                          activa=False)

    assert files_recurrents([despesa]) == [
        ["R/ MUTUA", "caixa", "salut", "mensual", "117.50", "118.43", 12, "2025-01-05", "2025-12-05", "acabat"]]


def _recurrent(import_mensual, concepte="x", banc="A"):
    from decimal import Decimal
    from domain import MovimentRecurrent
    return MovimentRecurrent(concepte=concepte, banc=banc, categoria="c", carrecs=5, import_habitual=Decimal(1),
                             import_mensual=Decimal(import_mensual), periodicitat="mensual",
                             primera=date(2025, 1, 1), darrera=date(2025, 6, 1), activa=True)


def _resultat_previsio(suposits=(), fixos_acabats=()):
    from decimal import Decimal
    from domain import Previsio
    from app import ResultatPrevisio, ResumPrevisio

    previsio = Previsio(date(2025, 6, 28), Decimal("7400"), Decimal("-312.5"),
                        (_recurrent(2000),), (_recurrent(800), _recurrent("50.5")), (), (), tuple(suposits),
                        Decimal(100), tuple(fixos_acabats))
    return ResultatPrevisio(previsio, {}, [
        ResumPrevisio(3, date(2025, 9, 28), Decimal("9000"), Decimal("173.21")),
        ResumPrevisio(6, date(2025, 12, 28), Decimal("10650.25"), Decimal("244.95"))])


CAPCALERA_RESUM = (
    "Saldo actual (2025-06-28): 7400.00 €\n"
    "Ingressos fixos: +2000.00 €/mes\n"
    "Despeses fixes: -850.50 €/mes\n"
    "Resta de moviments (mediana): -312.50 €/mes\n"
)
SALDOS_RESUM = (
    "\n"
    "Saldo previst (i rang probable):\n"
    "  d'aquí a 3 mesos (2025-09-28): 9000.00 € (entre 8826.79 i 9173.21)\n"
    "  d'aquí a 6 mesos (2025-12-28): 10650.25 € (entre 10405.30 i 10895.20)"
)


def test_text_resum_previsio():
    from infra.ui_freesimplegui import text_resum_previsio

    assert text_resum_previsio(_resultat_previsio()) == CAPCALERA_RESUM + SALDOS_RESUM


def test_text_resum_previsio_diu_quins_suposits_inclou():
    from decimal import Decimal
    from domain import Suposit, FixAcabat
    from infra.ui_freesimplegui import text_resum_previsio

    resultat = _resultat_previsio([Suposit("Pàrquing", Decimal(-120), "mensual", date(2025, 7, 1))],
                                  [FixAcabat("caixa", "R/ BRESSOL", date(2025, 8, 1))])

    assert text_resum_previsio(resultat) == CAPCALERA_RESUM + (
        "Inclou els supòsits: Pàrquing (-120.00 € mensual); R/ BRESSOL s'acaba el 2025-08-01\n"
    ) + SALDOS_RESUM


def test_files_fixos_acabats():
    from domain import FixAcabat
    from infra.ui_freesimplegui import files_fixos_acabats

    assert files_fixos_acabats([FixAcabat("caixa", "R/ BRESSOL", date(2027, 7, 31))]) == [
        ["R/ BRESSOL", "caixa", "2027-07-31"]]


def test_opcions_fixos_actius_per_triar_quin_s_acaba():
    from infra.ui_freesimplegui import opcions_fixos

    previsio = _resultat_previsio().previsio
    previsio = type(previsio)(**{**previsio.__dict__,
                                 "ingressos_fixos": (_recurrent(2000, "NOMINA", "unicaja"),),
                                 "despeses_fixes": (_recurrent("236.5", "R/ BRESSOL", "caixa"),)})

    assert opcions_fixos(previsio) == {
        "Ingrés · NOMINA (unicaja) · 2000.00 €/mes": ("unicaja", "NOMINA"),
        "Despesa · R/ BRESSOL (caixa) · 236.50 €/mes": ("caixa", "R/ BRESSOL"),
    }


def test_files_suposits():
    from decimal import Decimal
    from domain import Suposit
    from infra.ui_freesimplegui import files_suposits

    assert files_suposits([Suposit("Pàrquing", Decimal(-120), "mensual", date(2026, 11, 16)),
                           Suposit("Classes", Decimal("-50.5"), "trimestral", date(2026, 1, 10), date(2026, 12, 31))]) == [
        ["Pàrquing", "-120.00", "mensual", "2026-11-16", ""],
        ["Classes", "-50.50", "trimestral", "2026-01-10", "2026-12-31"]]


def test_llegir_suposit_dels_camps_del_formulari():
    from decimal import Decimal
    from domain import Suposit
    from infra.ui_freesimplegui import llegir_suposit

    assert llegir_suposit(" Pàrquing ", "-120,50", "mensual", "2026-11-16", "") == \
        Suposit("Pàrquing", Decimal("-120.50"), "mensual", date(2026, 11, 16))
    assert llegir_suposit("Classes", "50", "anual", "2026-01-10", "2027-12-31").data_fi == date(2027, 12, 31)


@pytest.mark.parametrize("import_, inici, fi", [
    ("abc", "2026-11-16", ""),
    ("-10", "", ""),
    ("-10", "16/11/2026", ""),
    ("-10", "2026-11-16", "malament"),
])
def test_llegir_suposit_amb_camps_dolents(import_, inici, fi):
    from domain import SupositInvalid
    from infra.ui_freesimplegui import llegir_suposit

    with pytest.raises(SupositInvalid):
        llegir_suposit("x", import_, "mensual", inici, fi)


def test_llegir_pagament_efectiu_dels_camps_del_formulari():
    from decimal import Decimal
    from domain import PagamentEfectiu
    from infra.ui_freesimplegui import llegir_pagament_efectiu

    assert llegir_pagament_efectiu("Neteja", "200,5", "mensual", "2025-01-15", "") == \
        PagamentEfectiu("Neteja", Decimal("200.5"), "mensual", date(2025, 1, 15))
    with pytest.raises(Exception):
        llegir_pagament_efectiu("Neteja", "dos-cents", "mensual", "2025-01-15", "")


def test_files_moviments_amb_el_balanc_total():
    from decimal import Decimal
    from domain import Moviment
    from infra.ui_freesimplegui import files_moviments

    moviments = [Moviment(date(2025, 1, 1), "Sou", 1000, 1000, "A", "nomina"),
                 Moviment(date(2025, 1, 2), "Super", -100.5, 400, "B", "alimentacio")]

    assert files_moviments(moviments, [Decimal(1000), Decimal("1400")]) == [
        ["2025-01-01", "Sou", "1000.00", Decimal(1000), "1000.00", "A", "nomina"],
        ["2025-01-02", "Super", "-100.50", Decimal(400), "1400.00", "B", "alimentacio"]]


def test_text_resum_previsio_amb_bancs_exclosos():
    from decimal import Decimal
    from app import ResultatPrevisio
    from infra.ui_freesimplegui import text_resum_previsio

    base = _resultat_previsio()
    resultat = ResultatPrevisio(base.previsio, {}, base.resum, {"SIALP_PIAS": Decimal(5000)})

    assert text_resum_previsio(resultat).startswith(
        "Saldo actual (2025-06-28): 7400.00 € (sense SIALP_PIAS: 5000.00 €; total 12400.00 €)\n")


def test_text_resum_previsio_diu_quines_categories_no_compten_a_la_resta():
    from app import ResultatPrevisio
    from infra.ui_freesimplegui import text_resum_previsio

    base = _resultat_previsio()
    previsio = type(base.previsio)(**{**base.previsio.__dict__, "categories_excloses": ("amortitzacio", "obres")})

    assert "Resta de moviments (mediana, sense amortitzacio, obres): -312.50 €/mes\n" in \
        text_resum_previsio(ResultatPrevisio(previsio, {}, base.resum))
