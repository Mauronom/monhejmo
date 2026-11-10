import json
from pathlib import Path
from infra import resoldre_directori_dades, RepositoriCategoria


def test_la_variable_d_entorn_te_prioritat(tmp_path):
    (tmp_path / "home" / ".comptes2").mkdir(parents=True)

    directori = resoldre_directori_dades(
        env={"COMPTES2_DADES": str(tmp_path / "meves")},
        home=tmp_path / "home",
        antic=tmp_path / "antic",
    )

    assert directori == tmp_path / "meves"


def test_fa_servir_comptes2_a_home_si_existeix(tmp_path):
    (tmp_path / "home" / ".comptes2").mkdir(parents=True)
    (tmp_path / "antic").mkdir()

    directori = resoldre_directori_dades(env={}, home=tmp_path / "home", antic=tmp_path / "antic")

    assert directori == tmp_path / "home" / ".comptes2"


def test_si_no_hi_ha_res_fa_servir_el_directori_antic(tmp_path):
    (tmp_path / "antic").mkdir()

    directori = resoldre_directori_dades(env={}, home=tmp_path / "home", antic=tmp_path / "antic")

    assert directori == tmp_path / "antic"


def test_si_no_existeix_cap_crea_comptes2_a_home(tmp_path):
    directori = resoldre_directori_dades(env={}, home=tmp_path / "home", antic=tmp_path / "antic")

    assert directori == tmp_path / "home" / ".comptes2"
    assert directori.is_dir()


def test_la_variable_d_entorn_expandeix_la_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    directori = resoldre_directori_dades(env={"COMPTES2_DADES": "~/bancs"}, home=tmp_path, antic=tmp_path / "antic")

    assert directori == tmp_path / "bancs"


def test_categories_sense_fitxer_comença_buit_i_el_crea_en_desar(tmp_path):
    directori = tmp_path / "dades"

    repo = RepositoriCategoria(directori=directori)
    assert repo.get_all() == {}

    repo.save("oci", ["cinema"])
    assert json.loads((directori / "categories.json").read_text(encoding="utf-8")) == {"oci": ["cinema"]}
