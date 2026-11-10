from datetime import date, timedelta
from decimal import Decimal
from domain import Moviment, CriterisRecurrents, detectar_recurrents, clau_concepte


def _mov(data, concepte, import_, banc="banc", categoria="altres"):
    return Moviment(data=data, concepte=concepte, import_=import_, balance=0, banc=banc, categoria=categoria)


def _mensuals(concepte, imports, any_=2025, mes_inici=1, dia=5, **kw):
    return [_mov(date(any_ + (mes_inici - 1 + i) // 12, (mes_inici - 1 + i) % 12 + 1, dia), concepte, imp, **kw)
            for i, imp in enumerate(imports)]


def _per_concepte(despeses):
    return {d.concepte: d for d in despeses}


def test_clau_concepte_treu_numeros_i_signes():
    assert clau_concepte("R/ E.B. - BRESSOL 2025") == "r e b bressol"
    assert clau_concepte("FINANCIERA NACIONAL    BANCO CETE123456-ES00000A0000") == \
        "financiera nacional banco cete esa"


def test_detecta_un_rebut_mensual_estable():
    moviments = _mensuals("R/ MUTUA 01/25", [-117, -117, -120, -117, -117, -117], categoria="salut")

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents())

    assert despesa.concepte == "R/ MUTUA 01/25"
    assert despesa.categoria == "salut"
    assert despesa.carrecs == 6
    assert despesa.import_habitual == Decimal("117.50")
    assert despesa.periodicitat == "mensual"
    assert despesa.primera == date(2025, 1, 5)
    assert despesa.darrera == date(2025, 6, 5)
    assert despesa.activa
    # 117.50 cada (151 dies / 5) = 30.2 dies
    assert despesa.import_mensual == Decimal("118.43")


def test_agrupa_conceptes_que_nomes_canvien_els_numeros():
    moviments = [_mov(date(2025, m, 1), f"R/ SOM CONNEXIO {m:02d}/2025", -43.5) for m in range(1, 6)]

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents())

    assert despesa.carrecs == 5
    assert despesa.concepte == "R/ SOM CONNEXIO 05/2025"  # el del darrer càrrec


def test_el_mateix_concepte_en_bancs_diferents_son_despeses_diferents():
    moviments = (_mensuals("PRESTEC", [-100] * 4, banc="a") + _mensuals("PRESTEC", [-100] * 4, banc="b"))

    assert sorted(d.banc for d in detectar_recurrents(moviments, CriterisRecurrents())) == ["a", "b"]


def test_ignora_ingressos_i_despeses_de_pocs_mesos():
    moviments = _mensuals("NOMINA", [2000] * 6) + _mensuals("GIMNAS", [-30] * 3)

    assert detectar_recurrents(moviments, CriterisRecurrents()) == []


def test_ignora_despeses_amb_imports_molt_variables():
    moviments = _mensuals("LIQUIDACIO TARGETA", [-50, -400, -120, -900, -30, -600])

    assert detectar_recurrents(moviments, CriterisRecurrents()) == []


def test_ignora_despeses_de_molts_cops_al_mes():
    # Un peatge del mateix import, però diversos cops cada mes
    moviments = [_mov(date(2025, m, d), "TUNELS", -5.28) for m in range(1, 7) for d in (3, 10, 17)]

    assert detectar_recurrents(moviments, CriterisRecurrents()) == []


def test_detecta_rebuts_bimestrals():
    moviments = [_mov(date(2025, m, 7), "R/ AIGUES DE BARCELONA", -52) for m in (1, 3, 5, 7, 9)]

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents())

    assert despesa.periodicitat == "bimestral"
    assert despesa.import_mensual == Decimal("26.06")  # 52 cada 60.75 dies


def test_una_despesa_que_ja_no_es_cobra_queda_com_a_acabada():
    moviments = _mensuals("R/ COTXE", [-105] * 6) + [_mov(date(2025, 12, 1), "SUPER", -10)]

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents())

    assert not despesa.activa


def test_la_data_de_referencia_decideix_si_encara_esta_activa():
    moviments = _mensuals("R/ COTXE", [-105] * 6)

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents(), data_referencia=date(2025, 12, 1))

    assert not despesa.activa


def test_incloure_afegeix_despeses_que_no_passarien_la_deteccio():
    gas = [_mov(date(2025, m, 10), "R/ COMERCIALIZADORA REGULADA, GAS", imp)
           for m, imp in ((1, -120), (3, -95), (5, -30), (7, -20), (9, -25), (11, -80))]

    assert detectar_recurrents(gas, CriterisRecurrents()) == []
    [despesa] = detectar_recurrents(gas, CriterisRecurrents(incloure=("regulada, gas",)))
    assert despesa.carrecs == 6


def test_excloure_treu_despeses_encara_que_siguin_regulars():
    moviments = _mensuals("TRANSF MENSUAL", [-2500] * 6) + _mensuals("R/ MUTUA", [-117] * 6)

    despeses = detectar_recurrents(moviments, CriterisRecurrents(excloure=("transf mensual",),
                                                                       incloure=("TRANSF",)))

    assert [d.concepte for d in despeses] == ["R/ MUTUA"]


def test_ordenades_actives_primer_i_per_import_mensual():
    moviments = (_mensuals("PETITA", [-10] * 6, mes_inici=7)
                 + _mensuals("GRAN", [-500] * 6, mes_inici=7)
                 + _mensuals("ACABADA", [-900] * 6))

    despeses = detectar_recurrents(moviments, CriterisRecurrents())

    assert [d.concepte for d in despeses] == ["GRAN", "PETITA", "ACABADA"]


def test_un_sol_carrec_no_es_fix_encara_que_s_inclogui():
    moviments = [_mov(date(2025, 3, 1), "R/ IBI", -600)]

    assert detectar_recurrents(moviments, CriterisRecurrents(incloure=("ibi",))) == []


def test_dos_carrecs_inclosos_amb_un_any_de_diferencia_son_anuals():
    moviments = [_mov(date(2025, 3, 1), "R/ IBI", -600), _mov(date(2026, 3, 1), "R/ IBI", -600)]

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents(incloure=("ibi",)))

    assert despesa.periodicitat == "anual"
    assert despesa.import_mensual == Decimal("50.04")  # 600 cada 365 dies


def test_separa_rebuts_diferents_amb_el_mateix_concepte():
    # Quota de la comunitat i una altra quota petita, cobrades el mateix dia amb el mateix concepte
    moviments = [_mov(date(2025, m, 1), "R/ FINQUES", imp) for m in range(1, 7) for imp in (-153, -13)]

    despeses = detectar_recurrents(moviments, CriterisRecurrents())

    assert [(d.import_habitual, d.periodicitat, d.carrecs) for d in despeses] == [
        (Decimal("153.00"), "mensual", 6), (Decimal("13.00"), "mensual", 6)]


def test_en_separar_els_imports_semblants_van_junts_i_els_puntuals_es_descarten():
    trimestres = (3, 6, 9, 12)
    moviments = ([_mov(date(2025, m, 3), "R/ AJUNTAMENT", -267.43) for m in trimestres[:2]]
                 + [_mov(date(2025, m, 3), "R/ AJUNTAMENT", -282.71) for m in trimestres[2:]]
                 + [_mov(date(2025, m, 3), "R/ AJUNTAMENT", -10.67) for m in trimestres]
                 + [_mov(date(2025, 7, 3), "R/ AJUNTAMENT", -25.24)])

    despeses = detectar_recurrents(moviments, CriterisRecurrents(incloure=("ajuntament",)))

    assert [(d.carrecs, d.periodicitat) for d in despeses] == [(4, "trimestral"), (4, "trimestral")]


def test_no_separa_els_carrecs_de_dies_diferents():
    # Liquidacions setmanals de targeta: alguns imports s'assemblen, però no són rebuts fixos
    moviments = [_mov(date(2025, m, d), "REC.MCARD", imp)
                 for m in range(1, 7)
                 for d, imp in ((3, -(150 + m)), (10, -10 * m), (17, -1000 * m))]

    assert detectar_recurrents(moviments, CriterisRecurrents()) == []


def test_amb_ingressos_detecta_els_ingressos_i_ignora_les_despeses():
    moviments = _mensuals("NOMINA", [2000, 2000, 2050, 2000, 2000]) + _mensuals("R/ MUTUA", [-117] * 5)

    [ingres] = detectar_recurrents(moviments, CriterisRecurrents(), ingressos=True)

    assert ingres.concepte == "NOMINA"
    assert ingres.import_habitual == Decimal("2010.00")
    assert ingres.activa


def test_amb_ingressos_tambe_separa_rebuts_del_mateix_dia():
    moviments = [_mov(date(2025, m, 28), "NOMINA", imp) for m in range(1, 7) for imp in (2000, 150)]

    ingressos = detectar_recurrents(moviments, CriterisRecurrents(), ingressos=True)

    assert [d.import_habitual for d in ingressos] == [Decimal("2000.00"), Decimal("150.00")]


def test_si_en_separar_no_queda_cap_rebut_regular_es_mante_tot_junt():
    # Una prestació inclosa a mà amb imports molt diferents, dos cops alguns mesos el mateix dia
    imports = [-2557, -2918, -3084, -3520, -2288, -4022, -612, -3897]
    dies = [date(2025, 4, 3), date(2025, 4, 30), date(2025, 4, 30), date(2025, 5, 30),
            date(2025, 5, 30), date(2025, 6, 30), date(2025, 6, 30), date(2025, 7, 31)]
    moviments = [_mov(d, "PRESTACIONES", imp) for d, imp in zip(dies, imports)]

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents(incloure=("prestaciones",)))

    assert despesa.carrecs == 8


def test_guarda_l_interval_i_els_moviments_originals():
    moviments = _mensuals("NOMINA", [2000] * 5)

    [ingres] = detectar_recurrents(moviments, CriterisRecurrents(), ingressos=True)

    assert ingres.interval_dies == Decimal(30)  # 120 dies / 4
    assert [m.import_ for m in ingres.moviments] == [Decimal(2000)] * 5  # amb el signe original
    assert all(any(m is original for original in moviments) for m in ingres.moviments)


def test_els_carrecs_de_cada_setmana_son_setmanals():
    moviments = [_mov(date(2025, 1, 2) + timedelta(days=7 * i), "NETEJA (efectiu)", -40) for i in range(10)]

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents(incloure=("(efectiu)",)))

    assert despesa.periodicitat == "setmanal"


def test_ajunta_conceptes_que_nomes_tenen_una_paraula_de_mes_al_final():
    # El banc de vegades talla el concepte de manera diferent: "... PUIG Pui" i "... PUIG"
    moviments = (_mensuals("BIZUM A: JOAN GARCIA PUIG Pui", [-120] * 2, mes_inici=7)
                 + _mensuals("BIZUM A: JOAN GARCIA PUIG", [-120] * 3, mes_inici=9))

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents())

    assert despesa.carrecs == 5
    assert despesa.concepte == "BIZUM A: JOAN GARCIA PUIG"  # el del darrer càrrec


def test_no_ajunta_conceptes_curts_ni_que_difereixen_en_mes_d_una_paraula():
    moviments = (_mensuals("R/ GAS", [-50] * 4) + _mensuals("R/ GAS NATURAL", [-50] * 4)
                 + _mensuals("BIZUM A: ANNA PUIG", [-30] * 4) + _mensuals("BIZUM A: ANNA PUIG FERRER ROCA", [-30] * 4))

    assert len(detectar_recurrents(moviments, CriterisRecurrents())) == 4


def test_despres_d_un_salt_llarg_l_import_i_l_interval_son_els_dels_carrecs_recents():
    # Una primera visita al març i, des del juliol, 120 € cada mes
    dates = [date(2026, 3, 11), date(2026, 7, 2), date(2026, 7, 31), date(2026, 9, 1), date(2026, 10, 1), date(2026, 11, 3)]
    moviments = [_mov(d, "BIZUM A: DENTISTA", -80 if i == 0 else -120) for i, d in enumerate(dates)]

    [despesa] = detectar_recurrents(moviments, CriterisRecurrents())

    assert despesa.periodicitat == "mensual"
    assert despesa.import_habitual == Decimal("120.00")
    assert despesa.import_mensual == Decimal("117.83")  # 120 cada 31 dies (2/7 a 3/11)
    assert despesa.carrecs == 6 and despesa.primera == date(2026, 3, 11)  # la sèrie sencera


def test_si_despres_del_salt_nomes_hi_ha_un_carrec_es_fa_servir_tota_la_serie():
    dates = [date(2025, m, 28) for m in range(1, 9)] + [date(2026, 10, 26)]
    moviments = [_mov(d, "NOMINA", 2000) for d in dates]

    [ingres] = detectar_recurrents(moviments, CriterisRecurrents(), ingressos=True)

    assert ingres.interval_dies == Decimal((date(2026, 10, 26) - date(2025, 1, 28)).days) / 8
