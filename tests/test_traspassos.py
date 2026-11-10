from datetime import date
from domain import Moviment, marcar_traspassos, CATEGORIA_TRASPAS
from app import CarregarMoviments, Recategoritzar, MovimentsSessio
from infra import MemoryCategoriesRepo


def _mov(data, concepte, import_, banc, categoria="altres"):
    return Moviment(data, concepte, import_, 0, banc, categoria)


def test_una_transferencia_que_surt_d_un_compte_i_entra_a_l_altre_es_un_traspas():
    sortida = _mov(date(2026, 4, 2), "TRANSF.SEPA NACIONAL   Transf agost 3", -1000, "unicaja")
    entrada = _mov(date(2026, 4, 3), "TRANSF CTE DE: ANNA SERRA", 1000, "caixa")
    altre = _mov(date(2026, 4, 3), "SUPER", -1000, "caixa", "alimentacio")

    resultat = marcar_traspassos([sortida, entrada, altre])

    assert [m.categoria for m in resultat] == [CATEGORIA_TRASPAS, CATEGORIA_TRASPAS, "alimentacio"]
    assert sortida.categoria == "altres"  # no modifica els originals


def test_no_es_traspas_si_l_import_o_els_dies_no_quadren_o_es_el_mateix_compte():
    moviments = [
        _mov(date(2026, 4, 2), "TRANSF a", -1000, "unicaja"), _mov(date(2026, 4, 3), "TRANSF b", 999, "caixa"),
        _mov(date(2026, 5, 1), "TRANSF c", -500, "unicaja"), _mov(date(2026, 5, 7), "TRANSF d", 500, "caixa"),
        _mov(date(2026, 6, 1), "TRANSF e", -300, "unicaja"), _mov(date(2026, 6, 1), "TRANSF f", 300, "unicaja"),
    ]

    assert {m.categoria for m in marcar_traspassos(moviments)} == {"altres"}


def test_cal_que_tots_dos_conceptes_siguin_transferencies():
    # Una aportació al SIALP i el seu moviment fictici quadren exactament, però no són traspassos
    moviments = [_mov(date(2026, 4, 2), "R/ Caja de Ingenieros Vida", -100, "caixa"),
                 _mov(date(2026, 4, 2), "SIALP PIES", 100, "SIALP_PIAS")]

    assert {m.categoria for m in marcar_traspassos(moviments)} == {"altres"}


def test_cada_moviment_nomes_fa_parella_una_vegada_i_amb_el_mes_proper():
    sortides = [_mov(date(2026, 4, 1), "TRANSF 1", -1000, "unicaja"), _mov(date(2026, 4, 9), "TRANSF 2", -1000, "unicaja")]
    entrades = [_mov(date(2026, 4, 2), "TRANSF DE 1", 1000, "caixa"), _mov(date(2026, 4, 10), "TRANSF DE 2", 1000, "caixa"),
                _mov(date(2026, 4, 3), "TRANSF DE 3", 1000, "caixa")]

    resultat = marcar_traspassos(sortides + entrades)

    assert [m.categoria == CATEGORIA_TRASPAS for m in resultat] == [True, True, True, True, False]


def test_la_carrega_i_la_recategoritzacio_marquen_els_traspassos():
    class Font:
        def llegir(self, directori):
            return [_mov(date(2026, 4, 2), "TRANSF.SEPA Transf set 1", -1000, "unicaja"),
                    _mov(date(2026, 4, 2), "TRANSF CTE DE: ANNA", 1000, "caixa")]

    sessio = MovimentsSessio()
    categories = MemoryCategoriesRepo({"transferencia": ["transf"]})
    carregats = CarregarMoviments(Font(), None, categories, sessio).execute("/d")
    recategoritzats = Recategoritzar(sessio, categories).execute()

    assert {m.categoria for m in carregats.moviments} == {CATEGORIA_TRASPAS}
    assert {m.categoria for m in recategoritzats.moviments} == {CATEGORIA_TRASPAS}
