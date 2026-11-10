from domain import FontMoviments
from infra import RepositoriMovimentsNorma43


def test_norma43_compleix_el_port():
    assert issubclass(RepositoriMovimentsNorma43, FontMoviments)
    assert FontMoviments.__abstractmethods__ == {"llegir"}
