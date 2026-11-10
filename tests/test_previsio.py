from datetime import date
from decimal import Decimal
from domain import (Moviment, MovimentRecurrent, CriterisRecurrents, ConfigPrevisio, sumar_mesos,
                    saldo_actual, moviments_fixos_previstos, variable_mensual, preveure)


def _mov(data, concepte, import_, balance=0, banc="A"):
    return Moviment(data=data, concepte=concepte, import_=import_, balance=balance, banc=banc)


def _amb_saldos(moviments, saldo=Decimal(0)):
    """Posa el saldo acumulat als moviments (d'un sol banc), en ordre de data."""
    resultat = []
    for m in sorted(moviments, key=lambda m: m.data):
        saldo += m.import_
        resultat.append(_mov(m.data, m.concepte, m.import_, saldo, m.banc))
    return resultat


def _recurrent(darrera, interval=30, activa=True, import_=100, concepte="R/ LLOGUER"):
    return MovimentRecurrent(concepte=concepte, banc="A", categoria="habitatge", carrecs=6,
                             import_habitual=Decimal(import_), import_mensual=Decimal(import_),
                             periodicitat="mensual", primera=date(2025, 1, 5), darrera=darrera,
                             activa=activa, interval_dies=Decimal(interval))


def test_sumar_mesos_ajusta_el_dia_al_final_del_mes():
    assert sumar_mesos(date(2025, 1, 31), 1) == date(2025, 2, 28)
    assert sumar_mesos(date(2025, 11, 15), 3) == date(2026, 2, 15)


def test_saldo_actual_suma_el_darrer_saldo_de_cada_banc():
    moviments = [_mov(date(2025, 1, 1), "x", 100, 100), _mov(date(2025, 1, 5), "y", 50, 150),
                 _mov(date(2025, 1, 3), "z", 50, 50, banc="B")]

    assert saldo_actual(moviments) == Decimal(200)


def test_els_fixos_es_repeteixen_des_del_darrer_carrec_amb_el_seu_interval():
    previstos = moviments_fixos_previstos([_recurrent(date(2025, 6, 5))], -1, date(2025, 6, 20), date(2025, 9, 20))

    assert [(d, c, i) for d, c, i in previstos] == [
        (date(2025, 7, 5), "R/ LLOGUER", Decimal(-100)),
        (date(2025, 8, 4), "R/ LLOGUER", Decimal(-100)),
        (date(2025, 9, 3), "R/ LLOGUER", Decimal(-100)),
    ]


def test_un_carrec_que_ja_hauria_d_haver_arribat_no_es_preveu_en_el_passat():
    previstos = moviments_fixos_previstos([_recurrent(date(2025, 6, 5))], 1, date(2025, 7, 20), date(2025, 9, 20))

    assert [d for d, _, _ in previstos] == [date(2025, 8, 4), date(2025, 9, 3)]


def test_els_fixos_que_ja_no_es_cobren_no_es_preveuen():
    assert moviments_fixos_previstos([_recurrent(date(2025, 6, 5), activa=False)], -1,
                                     date(2025, 6, 20), date(2025, 9, 20)) == []


def test_variable_mensual_es_la_mediana_dels_mesos_complets_sense_els_fixos():
    lloguer = [_mov(date(2025, m, 1), "R/ LLOGUER", -800) for m in range(4, 8)]
    recurrent = MovimentRecurrent(**{**_recurrent(date(2025, 7, 1)).__dict__, "moviments": tuple(lloguer)})
    super_ = [_mov(date(2025, 3, 10), "SUPER", -999),   # abans dels 3 mesos d'històric
              _mov(date(2025, 4, 10), "SUPER", -300), _mov(date(2025, 5, 10), "SUPER", -500),
              _mov(date(2025, 6, 10), "SUPER", -400), _mov(date(2025, 6, 12), "BIZUM", 50),
              _mov(date(2025, 7, 5), "SUPER", -999)]    # el mes en curs no és complet

    variable = variable_mensual(lloguer + super_, [recurrent], date(2025, 7, 10), mesos=3)

    assert variable == Decimal(-350)  # mediana de -300, -500 i -350


def test_variable_mensual_nomes_compta_els_mesos_amb_dades():
    moviments = [_mov(date(2025, 5, 10), "SUPER", -500), _mov(date(2025, 6, 10), "SUPER", -400)]

    assert variable_mensual(moviments, [], date(2025, 7, 10), mesos=12) == Decimal(-450)


def _historic():
    """Sis mesos: nòmina el 28, lloguer l'1 i súper dos cops al mes (sempre 300 € al mes)."""
    super_ = [(100, 200), (250, 50), (150, 150), (280, 20), (60, 240), (120, 180)]
    moviments = []
    for mes in range(1, 7):
        moviments += [_mov(date(2025, mes, 1), "R/ LLOGUER", -800),
                      _mov(date(2025, mes, 10), "SUPER", -super_[mes - 1][0]),
                      _mov(date(2025, mes, 20), "SUPER", -super_[mes - 1][1]),
                      _mov(date(2025, mes, 28), "NOMINA", 2000)]
    return _amb_saldos(moviments, Decimal(1000)) + [_mov(date(2025, 6, 1), "SIALP", 100, 5000, banc="SIALP")]


def test_preveure_parteix_del_saldo_actual_sense_els_bancs_exclosos():
    previsio = preveure(_historic(), CriterisRecurrents(), CriterisRecurrents(),
                        ConfigPrevisio(horitzo_mesos=2, bancs_exclosos=("SIALP",)))

    assert previsio.data_inici == date(2025, 6, 28)
    assert previsio.saldo_inicial == Decimal(1000 + 6 * (2000 - 800 - 300))
    assert [d.concepte for d in previsio.ingressos_fixos] == ["NOMINA"]
    assert [d.concepte for d in previsio.despeses_fixes] == ["R/ LLOGUER"]
    assert previsio.variable_mensual == Decimal(-300)


def test_preveure_suma_els_fixos_i_la_variable_de_cada_mes():
    previsio = preveure(_historic(), CriterisRecurrents(), CriterisRecurrents(),
                        ConfigPrevisio(horitzo_mesos=2, bancs_exclosos=("SIALP",)))

    assert [(m.data, m.concepte, m.import_) for m in previsio.moviments] == [
        (date(2025, 7, 1), "R/ LLOGUER", Decimal(-800)),
        (date(2025, 7, 28), "NOMINA", Decimal(2000)),
        (date(2025, 7, 28), "Despesa variable (mediana mensual)", Decimal(-300)),
        (date(2025, 7, 31), "R/ LLOGUER", Decimal(-800)),
        (date(2025, 8, 27), "NOMINA", Decimal(2000)),
        (date(2025, 8, 28), "Despesa variable (mediana mensual)", Decimal(-300)),
    ]
    assert previsio.moviments[-1].saldo == previsio.saldo_inicial + 2 * (2000 - 800 - 300)
    assert previsio.saldo_a(date(2025, 7, 15)) == previsio.saldo_inicial - 800
    assert previsio.saldo_a(date(2025, 6, 30)) == previsio.saldo_inicial


def test_preveure_sense_moviments():
    previsio = preveure([], CriterisRecurrents(), CriterisRecurrents(), ConfigPrevisio())

    assert previsio.moviments == () and previsio.saldo_inicial == Decimal(0)


# --- Supòsits -------------------------------------------------------------------------------

from domain import Suposit, SupositInvalid, validar_suposit, moviments_suposits
import pytest


def test_un_suposit_mensual_es_repeteix_des_de_la_data_d_inici():
    parquing = Suposit("Pàrquing", Decimal(-120), "mensual", date(2025, 7, 31))

    previstos = moviments_suposits([parquing], date(2025, 7, 1), date(2025, 10, 15))

    assert previstos == [(date(2025, 7, 31), "Pàrquing", Decimal(-120)),
                         (date(2025, 8, 31), "Pàrquing", Decimal(-120)),
                         (date(2025, 9, 30), "Pàrquing", Decimal(-120))]


def test_un_suposit_nomes_compta_dins_de_la_previsio_i_fins_a_la_data_fi():
    classes = Suposit("Classes", Decimal(-50), "trimestral", date(2025, 1, 10), data_fi=date(2025, 12, 31))

    previstos = moviments_suposits([classes], date(2025, 5, 1), date(2026, 6, 1))

    assert [d for d, _, _ in previstos] == [date(2025, 7, 10), date(2025, 10, 10)]


def test_un_suposit_puntual_nomes_passa_un_cop():
    viatge = Suposit("Viatge", Decimal(-2000), "puntual", date(2025, 8, 1))

    assert moviments_suposits([viatge], date(2025, 7, 1), date(2026, 7, 1)) == [
        (date(2025, 8, 1), "Viatge", Decimal(-2000))]
    assert moviments_suposits([viatge], date(2025, 9, 1), date(2026, 7, 1)) == []


@pytest.mark.parametrize("suposit", [
    Suposit("", Decimal(-10), "mensual", date(2025, 1, 1)),
    Suposit("x", Decimal(0), "mensual", date(2025, 1, 1)),
    Suposit("x", Decimal(-10), "quinzenal", date(2025, 1, 1)),
    Suposit("x", Decimal(-10), "mensual", date(2025, 6, 1), data_fi=date(2025, 1, 1)),
])
def test_suposits_invalids(suposit):
    with pytest.raises(SupositInvalid):
        validar_suposit(suposit)


def test_preveure_amb_suposits_dona_les_dues_linies():
    parquing = Suposit("Pàrquing", Decimal(-120), "mensual", date(2025, 7, 5))

    previsio = preveure(_historic(), CriterisRecurrents(), CriterisRecurrents(),
                        ConfigPrevisio(horitzo_mesos=2, bancs_exclosos=("SIALP",)), suposits=[parquing])

    assert "Pàrquing" not in [m.concepte for m in previsio.moviments]
    assert [m.concepte for m in previsio.moviments_amb_suposits].count("Pàrquing") == 2
    final = date(2025, 8, 28)
    assert previsio.saldo_a(final, amb_suposits=True) == previsio.saldo_a(final) - 240
    assert previsio.suposits == (parquing,)


def test_preveure_sense_suposits_les_dues_linies_son_iguals():
    previsio = preveure(_historic(), CriterisRecurrents(), CriterisRecurrents(), ConfigPrevisio(horitzo_mesos=2))

    assert previsio.moviments_amb_suposits == previsio.moviments


# --- Franja i fixos que s'acaben ------------------------------------------------------------

from datetime import timedelta
from domain import resta_mensual, amplada_mensual, FixAcabat, validar_fix_acabat


def test_resta_mensual_dona_el_net_de_cada_mes_del_mes_mes_antic_al_mes_recent():
    moviments = [_mov(date(2025, 4, 10), "SUPER", -300), _mov(date(2025, 5, 10), "SUPER", -500),
                 _mov(date(2025, 6, 10), "SUPER", -400), _mov(date(2025, 6, 12), "BIZUM", 50)]

    assert resta_mensual(moviments, [], date(2025, 7, 10), mesos=3) == [Decimal(-300), Decimal(-500), Decimal(-350)]


def test_amplada_mensual_es_la_meitat_del_rang_interquartilic():
    assert amplada_mensual([Decimal(-300), Decimal(-500), Decimal(-350), Decimal(-400)]) == Decimal("43.75")
    assert amplada_mensual([Decimal(-300)]) == Decimal(0)


def test_el_marge_creix_amb_l_arrel_dels_mesos():
    previsio = preveure(_historic(), CriterisRecurrents(), CriterisRecurrents(), ConfigPrevisio(horitzo_mesos=2))
    previsio = type(previsio)(**{**previsio.__dict__, "amplada_mensual": Decimal(100)})

    assert previsio.marge_a(previsio.data_inici) == Decimal(0)
    assert previsio.marge_a(previsio.data_inici + timedelta(days=122)) == Decimal("200.20")  # ~4 mesos


def test_preveure_calcula_l_amplada_amb_la_resta_dels_mesos_historics():
    previsio = preveure(_historic(), CriterisRecurrents(), CriterisRecurrents(), ConfigPrevisio(horitzo_mesos=2))

    assert previsio.amplada_mensual == Decimal(0)  # el súper és sempre 300 € al mes


def test_un_fix_que_s_acaba_desapareix_de_la_linia_amb_suposits():
    fi_lloguer = FixAcabat("A", "R/ LLOGUER", date(2025, 7, 15))

    previsio = preveure(_historic(), CriterisRecurrents(), CriterisRecurrents(),
                        ConfigPrevisio(horitzo_mesos=2, bancs_exclosos=("SIALP",)), fixos_acabats=[fi_lloguer])

    lloguers = [m.data for m in previsio.moviments_amb_suposits if m.concepte == "R/ LLOGUER"]
    assert lloguers == [date(2025, 7, 1)]  # el del 31 de juliol ja no hi és
    assert [m.data for m in previsio.moviments if m.concepte == "R/ LLOGUER"] == [date(2025, 7, 1), date(2025, 7, 31)]
    assert previsio.saldo_a(date(2025, 8, 28), amb_suposits=True) == previsio.saldo_a(date(2025, 8, 28)) + 800
    assert previsio.fixos_acabats == (fi_lloguer,)


def test_un_fix_acabat_es_reconeix_encara_que_el_concepte_canvii_de_numeros():
    fi = FixAcabat("A", "R/ LLOGUER 06/2025", date(2025, 6, 30))

    previsio = preveure(_historic(), CriterisRecurrents(), CriterisRecurrents(), ConfigPrevisio(horitzo_mesos=2),
                        fixos_acabats=[fi])

    assert "R/ LLOGUER" not in [m.concepte for m in previsio.moviments_amb_suposits]


@pytest.mark.parametrize("fix", [FixAcabat("", "R/ LLOGUER", date(2025, 7, 1)),
                                 FixAcabat("A", " ", date(2025, 7, 1)),
                                 FixAcabat("A", "R/ LLOGUER", None)])
def test_fixos_acabats_invalids(fix):
    with pytest.raises(SupositInvalid):
        validar_fix_acabat(fix)


def test_un_suposit_setmanal_es_repeteix_cada_set_dies():
    classes = Suposit("Classes", Decimal(-15), "setmanal", date(2025, 7, 3))

    previstos = moviments_suposits([classes], date(2025, 7, 1), date(2025, 7, 31))

    assert [d for d, _, _ in previstos] == [date(2025, 7, 3), date(2025, 7, 10), date(2025, 7, 17),
                                           date(2025, 7, 24), date(2025, 7, 31)]


# --- Categories excloses de la resta ----------------------------------------------------------

def test_les_categories_excloses_no_compten_a_la_resta_de_moviments():
    obres = [Moviment(date(2025, mes, 15), "REFORMA CUINA", -9000, 0, "A", "obres") for mes in (3, 4)]
    moviments = _historic() + obres
    config = ConfigPrevisio(horitzo_mesos=2, bancs_exclosos=("SIALP",))

    amb_obres = preveure(moviments, CriterisRecurrents(), CriterisRecurrents(), config)
    sense_obres = preveure(moviments, CriterisRecurrents(), CriterisRecurrents(),
                           ConfigPrevisio(horitzo_mesos=2, bancs_exclosos=("SIALP",), categories_excloses=("obres",)))

    assert amb_obres.amplada_mensual > 0          # el mes de les obres fa variar la resta
    assert sense_obres.amplada_mensual == 0       # sense les obres, tots els mesos són iguals
    assert sense_obres.variable_mensual == Decimal(-300)
    assert sense_obres.saldo_inicial == amb_obres.saldo_inicial  # el saldo actual sí que les té
    assert sense_obres.categories_excloses == ("obres",)
