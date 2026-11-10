from infra import MemoryCategoriesRepo


def test_instancies_sense_arguments_no_comparteixen_categories():
    repo_a = MemoryCategoriesRepo()
    repo_b = MemoryCategoriesRepo()

    repo_a.save("oci", ["cinema"])

    assert repo_b.get_all() == {}


def test_els_repositoris_de_categories_compleixen_el_port_sense_heretar_entre_ells():
    from domain import RepositoriCategories
    from infra import RepositoriCategoria

    assert RepositoriCategories.__abstractmethods__ == {"get_all", "save", "delete"}
    assert issubclass(MemoryCategoriesRepo, RepositoriCategories)
    assert issubclass(RepositoriCategoria, RepositoriCategories)
    assert not issubclass(RepositoriCategoria, MemoryCategoriesRepo)


def test_delete_retorna_si_existia():
    repo = MemoryCategoriesRepo({"oci": ["cinema"]})

    assert repo.delete("oci") is True
    assert repo.delete("oci") is False
