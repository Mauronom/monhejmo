import json
from datetime import date
from decimal import Decimal
from domain import Moviment, CriterisRecurrents, ConfigPrevisio, Suposit, FixAcabat
from app import PreveureSaldo, MovimentsSessio
from infra import (MemoryConfigRecurrentsRepo, JsonConfigPrevisioRepo, MemoryConfigPrevisioRepo,
                   MemoryRepositoriSuposits)


def _historic():
    moviments, saldo = [], Decimal(1000)
    for mes in range(1, 7):
        for dia, concepte, import_ in ((1, "R/ LLOGUER", -800), (28, "NOMINA", 2000)):
            saldo += import_
            moviments.append(Moviment(date(2025, mes, dia), concepte, import_, saldo, "A"))
    moviments.append(Moviment(date(2025, 6, 1), "SIALP", 100, 5000, "SIALP"))
    return moviments


def _cas(moviments, config=ConfigPrevisio(horitzo_mesos=6, bancs_exclosos=("SIALP",)), suposits=(),
         fixos_acabats=()):
    sessio = MovimentsSessio()
    sessio.substituir(moviments)
    return PreveureSaldo(sessio, MemoryConfigRecurrentsRepo(CriterisRecurrents()),
                         MemoryConfigRecurrentsRepo(CriterisRecurrents()), MemoryConfigPrevisioRepo(config),
                         MemoryRepositoriSuposits(list(suposits)), MemoryRepositoriSuposits(list(fixos_acabats)))


def test_la_grafica_te_el_total_real_i_la_previsio_que_hi_enllaça():
    resultat = _cas(_historic()).execute()

    punts = resultat.grafica["punts"]
    reals = [p for p in punts if p.banc == "Total"]
    previstos = [p for p in punts if p.banc == "Previsió"]
    assert {p.banc for p in punts} == {"Total", "Previsió"}  # sense el detall per banc ni el SIALP
    assert reals[-1].data == date(2025, 6, 28) and reals[-1].saldo == Decimal(1000 + 6 * 1200)
    # La previsió comença on acaba el real
    assert (previstos[0].data, previstos[0].saldo) == (reals[-1].data, reals[-1].saldo)
    assert previstos[-1].saldo == resultat.previsio.moviments_amb_suposits[-1].saldo
    assert resultat.grafica["linies_discontinues"] == ("Previsió",)


def test_el_resum_dona_el_saldo_previst_a_3_6_i_12_mesos_dins_de_l_horitzo():
    resultat = _cas(_historic()).execute()

    assert [(r.mesos, r.data) for r in resultat.resum] == [(3, date(2025, 9, 28)), (6, date(2025, 12, 28))]
    resum = resultat.resum[0]
    assert resum.saldo == resultat.previsio.saldo_a(resum.data, amb_suposits=True)
    assert resum.marge == resultat.previsio.marge_a(resum.data)


def test_la_previsio_ja_inclou_els_suposits():
    parquing = Suposit("Pàrquing", Decimal(-100), "mensual", date(2025, 7, 5))
    sense = _cas(_historic()).execute()

    resultat = _cas(_historic(), suposits=[parquing]).execute()

    assert {p.banc for p in resultat.grafica["punts"]} == {"Total", "Previsió"}  # una sola previsió
    assert "Pàrquing" in [p.concepte for p in resultat.grafica["punts"] if p.banc == "Previsió"]
    assert resultat.resum[0].saldo == sense.resum[0].saldo - 3 * 100  # juliol, agost i setembre


def test_la_previsio_ja_inclou_els_fixos_que_s_acaben():
    sense = _cas(_historic()).execute()

    resultat = _cas(_historic(), fixos_acabats=[FixAcabat("A", "R/ LLOGUER", date(2025, 7, 15))]).execute()

    assert resultat.resum[0].saldo > sense.resum[0].saldo


def test_la_franja_del_rang_probable_va_al_voltant_de_la_previsio_amb_suposits():
    parquing = Suposit("Pàrquing", Decimal(-100), "mensual", date(2025, 7, 5))

    resultat = _cas(_historic(), suposits=[parquing]).execute()

    [franja] = resultat.grafica["franges"]
    previsio = resultat.previsio
    assert franja["nom"] == "Rang probable"
    assert franja["dates"][0] == previsio.data_inici and date(2025, 7, 5) in franja["dates"]
    for data, baix, alt in zip(franja["dates"], franja["baix"], franja["alt"]):
        assert baix == previsio.saldo_a(data, amb_suposits=True) - previsio.marge_a(data)
        assert alt == previsio.saldo_a(data, amb_suposits=True) + previsio.marge_a(data)


def test_sense_moviments_no_hi_ha_previsio():
    resultat = _cas([]).execute()

    assert resultat.grafica["punts"] == [] and resultat.resum == [] and resultat.grafica["franges"] == []


def test_config_json_de_la_previsio(tmp_path):
    fitxer = tmp_path / "config.json"
    fitxer.write_text(json.dumps({"previsio": {"horitzo_mesos": 24, "bancs_exclosos": ["SIALP"],
                                               "categories_excloses": ["obres"]}}), encoding="utf-8")

    assert JsonConfigPrevisioRepo(fitxer).get_config() == ConfigPrevisio(
        horitzo_mesos=24, bancs_exclosos=("SIALP",), categories_excloses=("obres",))
    assert JsonConfigPrevisioRepo(tmp_path / "no_hi_es.json").get_config() == ConfigPrevisio()


def test_el_resultat_dona_el_saldo_dels_bancs_exclosos():
    resultat = _cas(_historic()).execute()

    assert resultat.saldos_exclosos == {"SIALP": Decimal(5000)}
