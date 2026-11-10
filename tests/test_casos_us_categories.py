import pytest
from domain import CategoriaInvalida, parsejar_paraules_clau
from app import AfegirCategoria, EditarCategoria, EliminarCategoria, LlistarCategories
from infra import MemoryCategoriesRepo


@pytest.fixture
def repo():
    return MemoryCategoriesRepo({
        "alimentació": ["supermercat", "fruits"],
        "transport": ["gasolina", "tren"],
    })


# --- parsejar_paraules_clau

@pytest.mark.parametrize("text, esperat", [
    ("supermercat, fruits", ["supermercat", "fruits"]),
    ("  a ,b,, c  ,", ["a", "b", "c"]),
    ("una", ["una"]),
    ("", []),
    (None, []),
    (" , , ", []),
])
def test_parsejar_paraules_clau(text, esperat):
    assert parsejar_paraules_clau(text) == esperat


# --- AfegirCategoria

def test_afegir_crea_la_categoria(repo):
    AfegirCategoria(repo).execute("oci", ["cinema", "teatre"])

    assert repo.get_all()["oci"] == ["cinema", "teatre"]


def test_afegir_categoria_existent_la_sobreescriu(repo):
    AfegirCategoria(repo).execute("transport", ["metro"])

    assert repo.get_all()["transport"] == ["metro"]


def test_afegir_sense_paraules_clau(repo):
    AfegirCategoria(repo).execute("buida", [])

    assert repo.get_all()["buida"] == []


def test_afegir_amb_caracters_especials(repo):
    AfegirCategoria(repo).execute("Oci & Cultura", ["cinema €", "l'Auditori"])

    assert repo.get_all()["Oci & Cultura"] == ["cinema €", "l'Auditori"]


@pytest.mark.parametrize("nom", ["", "   ", None])
def test_afegir_sense_nom_falla_i_no_desa_res(repo, nom):
    abans = dict(repo.get_all())

    with pytest.raises(CategoriaInvalida):
        AfegirCategoria(repo).execute(nom, ["x"])

    assert repo.get_all() == abans


# --- EditarCategoria

def test_editar_substitueix_les_paraules_clau(repo):
    EditarCategoria(repo).execute("transport", ["gasolina", "tren", "metro"])

    assert repo.get_all()["transport"] == ["gasolina", "tren", "metro"]


def test_editar_categoria_inexistent_la_crea(repo):
    EditarCategoria(repo).execute("nova", ["x"])

    assert repo.get_all()["nova"] == ["x"]


def test_editar_amb_paraules_buides(repo):
    EditarCategoria(repo).execute("transport", [])

    assert repo.get_all()["transport"] == []


@pytest.mark.parametrize("nom", ["", None])
def test_editar_sense_nom_falla(repo, nom):
    with pytest.raises(CategoriaInvalida):
        EditarCategoria(repo).execute(nom, ["x"])


# --- EliminarCategoria

def test_eliminar_categoria_existent(repo):
    assert EliminarCategoria(repo).execute("transport") is True
    assert "transport" not in repo.get_all()


def test_eliminar_categoria_inexistent_retorna_false(repo):
    assert EliminarCategoria(repo).execute("no existeix") is False
    assert len(repo.get_all()) == 2


def test_eliminar_distingeix_majuscules(repo):
    assert EliminarCategoria(repo).execute("Transport") is False
    assert "transport" in repo.get_all()


def test_eliminar_l_ultima_categoria():
    repo = MemoryCategoriesRepo({"única": ["x"]})

    assert EliminarCategoria(repo).execute("única") is True
    assert repo.get_all() == {}


# --- LlistarCategories

def test_llistar_retorna_totes_les_categories(repo):
    assert LlistarCategories(repo).execute() == {
        "alimentació": ["supermercat", "fruits"],
        "transport": ["gasolina", "tren"],
    }


def test_llistar_repositori_buit():
    assert LlistarCategories(MemoryCategoriesRepo()).execute() == {}


def test_llistar_retorna_una_copia(repo):
    categories = LlistarCategories(repo).execute()

    categories["transport"].append("modificat")
    del categories["alimentació"]

    assert repo.get_all() == {
        "alimentació": ["supermercat", "fruits"],
        "transport": ["gasolina", "tren"],
    }
