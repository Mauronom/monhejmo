import json
from datetime import date
from decimal import Decimal
from domain import Moviment, FiltreMoviments, CriterisRecurrents
from app import MovimentsRecurrents, MovimentsSessio
from infra import JsonConfigRecurrentsRepo, MemoryConfigRecurrentsRepo


def _mov(data, concepte, import_, categoria="altres"):
    return Moviment(data=data, concepte=concepte, import_=import_, balance=0, banc="banc", categoria=categoria)


MOVIMENTS = ([_mov(date(2025, m, 2), "R/ MUTUA", -100, "salut") for m in range(1, 13)]
             + [_mov(date(2025, m, 5), "R/ GIMNAS", -30, "oci") for m in range(1, 7)]
             + [_mov(date(2025, m, 8), "TRANSF MENSUAL", -2500) for m in range(1, 13)]
             + [_mov(date(2025, m, 28), "NOMINA", 2000, "nomina") for m in range(1, 13)])


def _cas(criteris=CriterisRecurrents(), moviments=MOVIMENTS, ingressos=False):
    sessio = MovimentsSessio()
    sessio.substituir(moviments)
    return MovimentsRecurrents(sessio, MemoryConfigRecurrentsRepo(criteris), ingressos=ingressos)


def test_retorna_les_despeses_fixes_i_l_import_mensual_de_les_actives():
    resultat = _cas(CriterisRecurrents(excloure=("transf mensual",))).execute(FiltreMoviments())

    assert [(d.concepte, d.activa) for d in resultat.recurrents] == [("R/ MUTUA", True), ("R/ GIMNAS", False)]
    assert resultat.import_mensual == resultat.recurrents[0].import_mensual


def test_amb_ingressos_retorna_els_ingressos_fixos():
    resultat = _cas(ingressos=True).execute(FiltreMoviments())

    assert [d.concepte for d in resultat.recurrents] == ["NOMINA"]
    assert resultat.recurrents[0].import_habitual == Decimal("2000.00")


def test_nomes_mira_els_moviments_del_filtre():
    resultat = _cas().execute(FiltreMoviments(categoria="salut"))

    assert [d.concepte for d in resultat.recurrents] == ["R/ MUTUA"]


def test_la_data_de_referencia_es_la_de_tots_els_moviments_no_la_dels_filtrats():
    # Filtrant pel gimnàs, el darrer moviment és del juny, però a la sessió n'hi ha fins al desembre
    resultat = _cas().execute(FiltreMoviments(text="gimnas"))

    assert not resultat.recurrents[0].activa


def test_amb_data_fi_es_mira_si_estaven_actives_en_aquella_data():
    resultat = _cas().execute(FiltreMoviments(text="gimnas", data_fi=date(2025, 6, 30)))

    assert resultat.recurrents[0].activa


def test_sense_moviments_no_hi_ha_res():
    resultat = _cas(moviments=[]).execute(FiltreMoviments())

    assert resultat.recurrents == [] and resultat.import_mensual == Decimal(0)


def test_config_json_llegeix_els_criteris_de_la_seccio_indicada(tmp_path):
    fitxer = tmp_path / "config.json"
    fitxer.write_text(json.dumps({
        "despeses_fixes": {"min_mesos": 3, "incloure": ["gas"], "excloure": ["transf", "bizum"]},
        "ingressos_fixos": {"incloure": ["nomina"]},
    }), encoding="utf-8")

    assert JsonConfigRecurrentsRepo(fitxer, "despeses_fixes").get_criteris() == \
        CriterisRecurrents(min_mesos=3, incloure=("gas",), excloure=("transf", "bizum"))
    assert JsonConfigRecurrentsRepo(fitxer, "ingressos_fixos").get_criteris() == \
        CriterisRecurrents(incloure=("nomina",))


def test_config_json_sense_la_seccio_fa_servir_els_valors_per_defecte(tmp_path):
    fitxer = tmp_path / "config.json"
    fitxer.write_text("{}", encoding="utf-8")

    assert JsonConfigRecurrentsRepo(fitxer, "despeses_fixes").get_criteris() == CriterisRecurrents()
    assert JsonConfigRecurrentsRepo(tmp_path / "no_existeix.json", "x").get_criteris() == CriterisRecurrents()
