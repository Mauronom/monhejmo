from datetime import date
from domain import Moviment, ReglaMovimentFictici, FontMoviments, CATEGORIA_PER_DEFECTE
from app import CarregarMoviments, Recategoritzar, MovimentsSessio
from infra import MemoryCategoriesRepo, MemoryConfigMovimentsFicticisRepo


class FontFalsa(FontMoviments):
    def __init__(self, moviments):
        self.moviments = moviments
        self.directori_llegit = None

    def llegir(self, directori):
        self.directori_llegit = directori
        return [m.clone() for m in self.moviments]


ORIGINALS = [
    Moviment(date(2025, 1, 5), "CI PIAS", -100, 4750, "Banc B"),
    Moviment(date(2025, 1, 1), "Sou", 2000, 5000, "Banc A"),
    Moviment(date(2025, 1, 2), "Compra supermercat", -50, 4950, "Banc A"),
    Moviment(date(2025, 1, 1), "Bizum", 10, 10, "Banc 0"),
]
CATEGORIES = {"ingrés": ["sou"], "alimentació": ["supermercat"], "estalvi": ["SIALP", "PIAS"]}
REGLA = ReglaMovimentFictici(patrons=["CI PIAS"], concepte_desti="SIALP PIES", banc_desti="SIALP_PIAS")
INICIAL = Moviment(date(2024, 8, 1), "SIALP PIES", 0, 10000, "SIALP_PIAS")


def _carregar(config=None, categories=CATEGORIES):
    font, sessio = FontFalsa(ORIGINALS), MovimentsSessio()
    cas_us = CarregarMoviments(font, config, MemoryCategoriesRepo(dict(categories)), sessio)
    return cas_us, font, sessio


def test_llegeix_del_directori_indicat():
    cas_us, font, _ = _carregar()

    cas_us.execute("/dades")

    assert font.directori_llegit == "/dades"


def test_afegeix_els_ficticis_categoritza_i_ordena():
    cas_us, _, _ = _carregar(MemoryConfigMovimentsFicticisRepo([REGLA], [INICIAL]))

    resultat = cas_us.execute("/dades")

    assert [(m.data, m.concepte, m.banc, m.categoria) for m in resultat.moviments] == [
        (date(2024, 8, 1), "SIALP PIES", "SIALP_PIAS", "estalvi"),
        (date(2025, 1, 1), "Bizum", "Banc 0", CATEGORIA_PER_DEFECTE),
        (date(2025, 1, 1), "Sou", "Banc A", "ingrés"),
        (date(2025, 1, 2), "Compra supermercat", "Banc A", "alimentació"),
        (date(2025, 1, 5), "CI PIAS", "Banc B", "estalvi"),
        (date(2025, 1, 5), "SIALP PIES", "SIALP_PIAS", "estalvi"),
    ]
    assert resultat.resum.total == 1960  # -100 + 2000 - 50 + 10 + 100 (el fictici); l'inicial té import 0


def test_sense_configuracio_nomes_els_moviments_llegits():
    cas_us, _, _ = _carregar(config=None)

    assert len(cas_us.execute("/dades").moviments) == 4


def test_desa_el_resultat_a_la_sessio():
    cas_us, _, sessio = _carregar(MemoryConfigMovimentsFicticisRepo([REGLA], [INICIAL]))

    resultat = cas_us.execute("/dades")

    assert sessio.actuals() == resultat.moviments


def test_recategoritzar_aplica_les_categories_actuals_a_la_sessio():
    repo_cats = MemoryCategoriesRepo(dict(CATEGORIES))
    sessio = MovimentsSessio()
    CarregarMoviments(FontFalsa(ORIGINALS), None, repo_cats, sessio).execute("/dades")

    repo_cats.save("transferències", ["bizum"])
    repo_cats.delete("ingrés")
    resultat = Recategoritzar(sessio, repo_cats).execute()

    categories = {m.concepte: m.categoria for m in sessio.actuals()}
    assert categories["Bizum"] == "transferències"
    assert categories["Sou"] == CATEGORIA_PER_DEFECTE
    assert resultat.moviments == sessio.actuals()


def test_recategoritzar_conserva_la_resta_de_camps():
    repo_cats = MemoryCategoriesRepo({})
    sessio = MovimentsSessio()
    sessio.substituir(ORIGINALS)

    Recategoritzar(sessio, repo_cats).execute()

    assert [(m.data, m.concepte, m.import_, m.balance, m.banc) for m in sessio.actuals()] == \
           sorted([(m.data, m.concepte, m.import_, m.balance, m.banc) for m in ORIGINALS], key=lambda t: (t[0], t[4]))


def test_la_sessio_retorna_copies():
    sessio = MovimentsSessio()
    sessio.substituir(ORIGINALS)

    sessio.actuals()[0].categoria = "modificada"
    ORIGINALS[0].categoria = "modificada"

    assert all(m.categoria == CATEGORIA_PER_DEFECTE for m in sessio.actuals())
    ORIGINALS[0].categoria = CATEGORIA_PER_DEFECTE
