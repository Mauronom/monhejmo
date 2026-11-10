import json
from datetime import date
from decimal import Decimal
import pytest
from domain import Suposit, SupositInvalid
from app import LlistarSuposits, AfegirSuposit, EliminarSuposit
from infra import JsonRepositoriSuposits, MemoryRepositoriSuposits

PARQUING = Suposit("Pàrquing", Decimal("-120.50"), "mensual", date(2026, 11, 16))
VIATGE = Suposit("Viatge", Decimal(-2000), "puntual", date(2027, 7, 1), data_fi=None)


def test_afegir_llistar_i_eliminar():
    repo = MemoryRepositoriSuposits()

    AfegirSuposit(repo).execute(PARQUING)
    AfegirSuposit(repo).execute(VIATGE)
    assert LlistarSuposits(repo).execute() == [PARQUING, VIATGE]

    assert EliminarSuposit(repo).execute(0)
    assert LlistarSuposits(repo).execute() == [VIATGE]
    assert not EliminarSuposit(repo).execute(5)


def test_no_s_afegeixen_suposits_invalids():
    repo = MemoryRepositoriSuposits()

    with pytest.raises(SupositInvalid):
        AfegirSuposit(repo).execute(Suposit("", Decimal(-1), "mensual", date(2026, 1, 1)))
    assert LlistarSuposits(repo).execute() == []


def test_json_desa_els_suposits_dins_de_previsio_sense_tocar_la_resta(tmp_path):
    fitxer = tmp_path / "config.json"
    fitxer.write_text(json.dumps({"previsio": {"horitzo_mesos": 24}, "altres": [1]}), encoding="utf-8")
    repo = JsonRepositoriSuposits(fitxer)

    repo.save_all([PARQUING, Suposit("Classes", Decimal(-50), "trimestral", date(2026, 1, 10), date(2026, 12, 31))])

    config = json.loads(fitxer.read_text(encoding="utf-8"))
    assert config["altres"] == [1] and config["previsio"]["horitzo_mesos"] == 24
    assert config["previsio"]["suposits"][0] == {
        "concepte": "Pàrquing", "import": "-120.50", "periodicitat": "mensual", "inici": "2026-11-16", "fi": None}
    assert JsonRepositoriSuposits(fitxer).get_all() == [
        PARQUING, Suposit("Classes", Decimal(-50), "trimestral", date(2026, 1, 10), date(2026, 12, 31))]


def test_json_sense_fitxer_no_hi_ha_suposits(tmp_path):
    assert JsonRepositoriSuposits(tmp_path / "config.json").get_all() == []


def test_acabar_fixos_llistar_i_eliminar():
    from domain import FixAcabat
    from app import LlistarFixosAcabats, AcabarFix, EliminarFixAcabat
    repo = MemoryRepositoriSuposits()
    bressol = FixAcabat("caixa", "R/ ESCOLA BRESSOL", date(2027, 7, 31))

    AcabarFix(repo).execute(bressol)
    assert LlistarFixosAcabats(repo).execute() == [bressol]
    with pytest.raises(SupositInvalid):
        AcabarFix(repo).execute(FixAcabat("caixa", "", date(2027, 7, 31)))
    assert EliminarFixAcabat(repo).execute(0)
    assert LlistarFixosAcabats(repo).execute() == []


def test_json_desa_els_fixos_acabats_al_costat_dels_suposits(tmp_path):
    from domain import FixAcabat
    from infra import JsonRepositoriFixosAcabats
    fitxer = tmp_path / "config.json"
    JsonRepositoriSuposits(fitxer).save_all([PARQUING])
    bressol = FixAcabat("caixa", "R/ ESCOLA BRESSOL", date(2027, 7, 31))

    JsonRepositoriFixosAcabats(fitxer).save_all([bressol])

    config = json.loads(fitxer.read_text(encoding="utf-8"))
    assert config["previsio"]["fixos_acabats"] == [
        {"banc": "caixa", "concepte": "R/ ESCOLA BRESSOL", "fi": "2027-07-31"}]
    assert JsonRepositoriSuposits(fitxer).get_all() == [PARQUING]
    assert JsonRepositoriFixosAcabats(fitxer).get_all() == [bressol]
