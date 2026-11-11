import json
from datetime import date
from decimal import Decimal
from domain import Moviment, FiltreMoviments, CriterisRecurrents, CriterisDespesesVariables
from app import CalcularDespesesVariables, MovimentsSessio
from infra import (MemoryConfigRecurrentsRepo, JsonConfigDespesesVariablesRepo,
                   MemoryConfigDespesesVariablesRepo)


def _mov(data, concepte, import_, categoria):
    return Moviment(data=data, concepte=concepte, import_=Decimal(import_), balance=0, banc="banc",
                    categoria=categoria)


MUTUA = [_mov(date(2025, m, 2), "R/ MUTUA", "-60", "salut") for m in range(1, 13)]
# Imports prou diferents perquè no sigui una despesa fixa
SUPERMERCAT = [_mov(date(2025, m, 10), "SUPERMERCAT", import_, "alimentacio")
               for m, import_ in ((1, "-20"), (4, "-150"), (7, "-40"), (12, "-190"))]
FARMACIA = _mov(date(2025, 12, 5), "FARMACIA", "-15", "salut")


def _cas(moviments, criteris=CriterisDespesesVariables()):
    sessio = MovimentsSessio()
    sessio.substituir(moviments)
    return CalcularDespesesVariables(sessio, MemoryConfigRecurrentsRepo(CriterisRecurrents()),
                                     MemoryConfigDespesesVariablesRepo(criteris))


def test_treu_les_despeses_fixes_i_reparteix_pel_periode_del_filtre():
    filtre = FiltreMoviments(data_inici=date(2025, 1, 1), data_fi=date(2025, 12, 31))

    resultat = _cas(MUTUA + SUPERMERCAT + [FARMACIA]).execute(filtre)

    assert [(c.categoria, c.total) for c in resultat.per_categoria] == [
        ("alimentacio", Decimal(400)), ("salut", Decimal(15))]
    assert resultat.mesos == Decimal("11.99")


def test_les_fixes_es_detecten_amb_tots_els_moviments_encara_que_el_filtre_sigui_curt():
    # Només el desembre: hi ha una sola quota de la mútua, però continua sent fixa
    filtre = FiltreMoviments(data_inici=date(2025, 12, 1), data_fi=date(2025, 12, 31))

    resultat = _cas(MUTUA + SUPERMERCAT + [FARMACIA]).execute(filtre)

    assert [(c.categoria, c.total) for c in resultat.per_categoria] == [
        ("alimentacio", Decimal(190)), ("salut", Decimal(15))]


def test_fa_servir_els_criteris_de_la_configuracio():
    criteris = CriterisDespesesVariables(categories_excloses=("salut",))

    resultat = _cas(MUTUA + SUPERMERCAT + [FARMACIA], criteris).execute(FiltreMoviments())

    assert [c.categoria for c in resultat.per_categoria] == ["alimentacio"]


def test_sense_moviments_no_hi_ha_res():
    resultat = _cas([]).execute(FiltreMoviments())

    assert resultat.per_categoria == [] and resultat.total == 0


def test_llegeix_els_criteris_de_config_json(tmp_path):
    fitxer = tmp_path / "config.json"
    fitxer.write_text(json.dumps({"despeses_variables": {"llindar_puntual": 750.5,
                                                         "categories_excloses": ["estalvi"]}}))

    assert JsonConfigDespesesVariablesRepo(fitxer).get_criteris() == CriterisDespesesVariables(
        llindar_puntual=Decimal("750.5"), categories_excloses=("estalvi",))


def test_sense_la_seccio_o_el_fitxer_els_criteris_per_defecte(tmp_path):
    fitxer = tmp_path / "config.json"
    fitxer.write_text("{}")

    assert JsonConfigDespesesVariablesRepo(fitxer).get_criteris() == CriterisDespesesVariables()
    assert JsonConfigDespesesVariablesRepo(tmp_path / "no_hi_es.json").get_criteris() == CriterisDespesesVariables()
