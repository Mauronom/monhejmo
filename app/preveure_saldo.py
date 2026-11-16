from collections import defaultdict
from dataclasses import dataclass, field, replace
from typing import Dict, List, NamedTuple
from datetime import date
from decimal import Decimal
from domain import PuntGrafica, Previsio, Suposit, calcular_punts, preveure, sumar_mesos, es_dins_algun

BANC_PREVISIO = "Previsió"
MESOS_PREVISIO_PASSADA = 6
BANC_PREVISIO_PASSADA = f"Previsió de fa {MESOS_PREVISIO_PASSADA} mesos"
FRANJA = "Rang probable"
MESOS_RESUM = (3, 6, 12)


class ResumPrevisio(NamedTuple):
    mesos: int
    data: date
    saldo: Decimal  # previst, amb els supòsits
    marge: Decimal  # del rang probable: saldo ± marge


@dataclass(frozen=True)
class ResultatPrevisio:
    previsio: Previsio
    grafica: dict  # com les altres gràfiques: punts i etiquetes, i la franja del rang probable
    resum: List[ResumPrevisio]  # a 3, 6 i 12 mesos, dins de l'horitzó
    saldos_exclosos: Dict[str, Decimal] = field(default_factory=dict)  # darrer saldo dels bancs exclosos


def _punts_previsio(previsio, banc=BANC_PREVISIO, moviments=None):
    """
    Punts de la previsió (per defecte, amb supòsits), començant pel saldo actual perquè enllaci amb
    el real.
    """
    moviments = previsio.moviments_amb_suposits if moviments is None else moviments
    punts = [PuntGrafica(previsio.data_inici, 0, previsio.saldo_inicial, banc, "Saldo actual", Decimal(0))]
    ordre_del_dia = defaultdict(int)
    for m in moviments:
        ordre_del_dia[m.data] += 1  # el punt inicial ja ocupa l'ordre 0 del primer dia
        punts.append(PuntGrafica(m.data, ordre_del_dia[m.data], m.saldo, banc, m.concepte, m.import_))
    return punts


def _franja(previsio):
    """Rang probable al voltant de la previsió (amb supòsits), un punt per dia amb moviments."""
    dates = sorted({previsio.data_inici} | {m.data for m in previsio.moviments_amb_suposits})
    saldos = [previsio.saldo_a(d, amb_suposits=True) for d in dates]
    marges = [previsio.marge_a(d) for d in dates]
    return {"nom": FRANJA, "color": "gray", "dates": dates,
            "baix": [s - m for s, m in zip(saldos, marges)], "alt": [s + m for s, m in zip(saldos, marges)]}


def _punts_previsio_passada(moviments, criteris_despeses, criteris_ingressos, config):
    """
    La previsió que s'hauria fet fa MESOS_PREVISIO_PASSADA mesos (amb només els moviments d'abans),
    fins avui: es veu al costat del saldo real per saber si la previsió és fiable. Els moviments de
    les categories excloses que hi ha hagut des de llavors (p. ex. obres) hi entren com a supòsits,
    tal com s'haurien hagut d'entrar, perquè la comparació sigui justa. Cap punt si no hi ha
    moviments d'abans.
    """
    avui = max(m.data for m in moviments)
    tall = sumar_mesos(avui, -MESOS_PREVISIO_PASSADA)
    passats = [m for m in moviments if m.data <= tall]
    if not passats:
        return []
    inici = max(m.data for m in passats)
    excloses = [Suposit(m.concepte, m.import_, "puntual", m.data) for m in moviments
                if inici < m.data <= avui and es_dins_algun(m.categoria, config.categories_excloses)]
    # Un mes més, perquè el darrer moviment d'abans del tall pot ser uns dies anterior; es talla a avui
    previsio = preveure(passats, criteris_despeses, criteris_ingressos,
                        replace(config, horitzo_mesos=MESOS_PREVISIO_PASSADA + 1), excloses, calibrar=False)
    return _punts_previsio(previsio, BANC_PREVISIO_PASSADA,
                           [m for m in previsio.moviments_amb_suposits if m.data <= avui])


class PreveureSaldo:
    """
    Previsió del saldo total a partir de tots els moviments de la sessió (no del filtre), sempre
    amb els supòsits (moviments nous i fixos que s'acaben): retorna la previsió, la gràfica
    (saldo total real, previsió i rang probable) i el saldo previst a 3, 6 i 12 mesos.
    """

    def __init__(self, sessio, config_despeses, config_ingressos, config_previsio, repositori_suposits,
                 repositori_fixos_acabats):
        self._sessio = sessio
        self._config_despeses = config_despeses
        self._config_ingressos = config_ingressos
        self._config_previsio = config_previsio
        self._suposits = repositori_suposits
        self._fixos_acabats = repositori_fixos_acabats

    def execute(self):
        config = self._config_previsio.get_config()
        tots = self._sessio.actuals()
        moviments = [m for m in tots if m.banc not in config.bancs_exclosos]
        saldos_exclosos = {}
        for m in sorted(tots, key=lambda m: m.data):  # el darrer saldo de cada banc exclòs
            if m.banc in config.bancs_exclosos:
                saldos_exclosos[m.banc] = m.balance
        previsio = preveure(moviments, self._config_despeses.get_criteris(),
                            self._config_ingressos.get_criteris(), config, self._suposits.get_all(),
                            self._fixos_acabats.get_all())

        punts = [p for p in calcular_punts(moviments) if p.banc == "Total"]
        discontinues, franges = (), []
        if previsio.data_inici:
            punts += _punts_previsio(previsio)
            discontinues = (BANC_PREVISIO,)
            franges = [_franja(previsio)]
            passada = _punts_previsio_passada(moviments, self._config_despeses.get_criteris(),
                                              self._config_ingressos.get_criteris(), config)
            if passada:
                punts += passada
                discontinues += (BANC_PREVISIO_PASSADA,)

        resum = [ResumPrevisio(mesos, data, previsio.saldo_a(data, amb_suposits=True), previsio.marge_a(data))
                 for mesos in MESOS_RESUM if mesos <= config.horitzo_mesos and previsio.data_inici
                 for data in [sumar_mesos(previsio.data_inici, mesos)]]
        grafica = {
            "punts": punts,
            "etiqueta_x": "Data",
            "etiqueta_y": "Saldo total",
            "titol": "Previsió del saldo total",
            "linies_discontinues": discontinues,
            "franges": franges,
        }
        return ResultatPrevisio(previsio, grafica, resum, saldos_exclosos)
