import calendar
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Tuple
from .recurrents import detectar_recurrents, clau_concepte, DIES_PER_MES, CENTIMS

CONCEPTE_VARIABLE = "Despesa variable (mediana mensual)"
MESOS_PER_PERIODICITAT = {"puntual": 0, "mensual": 1, "bimestral": 2, "trimestral": 3,
                          "semestral": 6, "anual": 12}
PERIODICITATS = ("puntual", "setmanal") + tuple(p for p in MESOS_PER_PERIODICITAT if p != "puntual")


class SupositInvalid(ValueError):
    pass


@dataclass(frozen=True)
class Suposit:
    """Un moviment que encara no existeix: puntual o recurrent des de data_inici fins a data_fi."""
    concepte: str
    import_: Decimal  # negatiu si és una despesa
    periodicitat: str  # una de PERIODICITATS
    data_inici: date
    data_fi: Optional[date] = None


@dataclass(frozen=True)
class FixAcabat:
    """Supòsit: un ingrés o despesa fix (banc i concepte) que ja no es cobrarà després de data_fi."""
    banc: str
    concepte: str
    data_fi: date


@dataclass(frozen=True)
class ConfigPrevisio:
    """
    - horitzo_mesos: quants mesos endavant es preveu.
    - mesos_historic: quants mesos complets enrere es miren per calcular la despesa variable.
    - bancs_exclosos: bancs que no compten (p. ex. productes d'estalvi que no són diners disponibles).
    - categories_excloses: categories de despeses puntuals (p. ex. amortitzacions anticipades,
      obres) que no compten per calcular la resta de moviments; si se'n preveuen, es posen com a supòsit.
    """
    horitzo_mesos: int = 12
    mesos_historic: int = 12
    bancs_exclosos: Tuple[str, ...] = ()
    categories_excloses: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MovimentPrevist:
    data: date
    concepte: str
    import_: Decimal
    saldo: Decimal  # saldo previst després d'aquest moviment


@dataclass(frozen=True)
class Previsio:
    data_inici: Optional[date]
    saldo_inicial: Decimal
    variable_mensual: Decimal  # net: negatiu si és despesa
    ingressos_fixos: Tuple    # MovimentRecurrent actius
    despeses_fixes: Tuple
    moviments: Tuple[MovimentPrevist, ...]                  # sense els supòsits
    moviments_amb_suposits: Tuple[MovimentPrevist, ...] = ()
    suposits: Tuple[Suposit, ...] = ()
    amplada_mensual: Decimal = Decimal(0)  # meitat del rang interquartílic de la resta mensual
    fixos_acabats: Tuple[FixAcabat, ...] = ()
    categories_excloses: Tuple[str, ...] = ()  # les que no compten a la resta de moviments

    @property
    def te_suposits(self):
        return bool(self.suposits or self.fixos_acabats)

    def marge_a(self, data):
        """
        Marge del rang probable (~50%) al voltant del saldo previst: creix amb l'arrel dels mesos
        transcorreguts, perquè els mesos bons i dolents es compensen en part.
        """
        if not self.data_inici or data <= self.data_inici:
            return Decimal(0)
        mesos = Decimal((data - self.data_inici).days) / DIES_PER_MES
        return (self.amplada_mensual * mesos.sqrt()).quantize(CENTIMS)

    def saldo_a(self, data, amb_suposits=False):
        """Saldo previst al final del dia indicat."""
        saldo = self.saldo_inicial
        for m in (self.moviments_amb_suposits if amb_suposits else self.moviments):
            if m.data > data:
                break
            saldo = m.saldo
        return saldo


def sumar_mesos(data, mesos):
    """La mateixa data uns quants mesos després; si el dia no existeix, el darrer del mes."""
    any_, mes = divmod(data.month - 1 + mesos, 12)
    any_, mes = data.year + any_, mes + 1
    return date(any_, mes, min(data.day, calendar.monthrange(any_, mes)[1]))


def saldo_actual(moviments):
    """Suma del darrer saldo de cada banc."""
    darrer = {}
    for m in sorted(moviments, key=lambda m: m.data):
        darrer[m.banc] = m.balance
    return sum(darrer.values(), Decimal(0))


def moviments_fixos_previstos(recurrents, signe, data_inici, data_fi, fixos_acabats=()):
    """
    Càrrecs futurs (data, concepte, import) dels recurrents actius entre data_inici (exclosa) i
    data_fi (inclosa): des del darrer càrrec, cada interval_dies. signe: 1 ingressos, -1 despeses.
    Els que estan a fixos_acabats ja no es cobren després de la seva data de fi.
    """
    previstos = []
    for r in recurrents:
        if not r.activa:
            continue
        fi_del_fix = _data_fi_del_fix(r, fixos_acabats)
        fi = min(data_fi, fi_del_fix) if fi_del_fix else data_fi
        k = 1
        while (data := r.darrera + timedelta(days=round(k * r.interval_dies))) <= fi:
            if data > data_inici:
                previstos.append((data, r.concepte, signe * r.import_habitual))
            k += 1
    return sorted(previstos, key=lambda p: p[0])


def validar_suposit(suposit):
    if not suposit.concepte.strip():
        raise SupositInvalid("Cal un concepte.")
    if suposit.import_ == 0:
        raise SupositInvalid("L'import no pot ser zero.")
    if suposit.periodicitat not in PERIODICITATS:
        raise SupositInvalid(f"Periodicitat desconeguda: {suposit.periodicitat}.")
    if suposit.data_fi and suposit.data_fi < suposit.data_inici:
        raise SupositInvalid("La data de fi és anterior a la d'inici.")


def validar_fix_acabat(fix):
    if not fix.banc.strip() or not fix.concepte.strip():
        raise SupositInvalid("Cal triar quin ingrés o despesa fix s'acaba.")
    if fix.data_fi is None:
        raise SupositInvalid("Cal la data a partir de la qual ja no es cobra.")


def _data_fi_del_fix(recurrent, fixos_acabats):
    """La data de fi més aviat dels supòsits que acaben aquest recurrent, o None."""
    dates = [f.data_fi for f in fixos_acabats
             if f.banc == recurrent.banc and clau_concepte(f.concepte) == clau_concepte(recurrent.concepte)]
    return min(dates) if dates else None


def dates_periodiques(inici, periodicitat, fi):
    """
    Dates des d'inici fins a fi (inclosa) amb la periodicitat indicada. Les mensuals i més llargues
    es calculen sumant mesos a la data d'inici (el dia 31 passa al darrer dia dels mesos curts).
    """
    if periodicitat == "setmanal":
        data = inici
        while data <= fi:
            yield data
            data += timedelta(days=7)
        return
    pas = MESOS_PER_PERIODICITAT[periodicitat]
    k = 0
    while (data := sumar_mesos(inici, k * pas)) <= fi:
        yield data
        if pas == 0:
            break
        k += 1


def moviments_suposits(suposits, data_inici, data_fi):
    """Moviments (data, concepte, import) dels supòsits entre data_inici (exclosa) i data_fi (inclosa)."""
    previstos = []
    for s in suposits:
        fi = min(data_fi, s.data_fi) if s.data_fi else data_fi
        previstos += [(data, s.concepte, s.import_) for data in dates_periodiques(s.data_inici, s.periodicitat, fi)
                      if data > data_inici]
    return sorted(previstos, key=lambda p: p[0])


def _acumular(saldo, futurs):
    """MovimentPrevist amb el saldo acumulat; el mateix dia, en l'ordre en què arriben."""
    previstos = []
    for data, concepte, import_ in sorted(futurs, key=lambda f: f[0]):
        saldo += import_
        previstos.append(MovimentPrevist(data, concepte, import_, saldo))
    return tuple(previstos)


def _mes(data):
    return (data.year, data.month)


def variable_mensual(moviments, recurrents, data_referencia, mesos):
    """Mediana de resta_mensual."""
    nets = resta_mensual(moviments, recurrents, data_referencia, mesos)
    return Decimal(statistics.median(nets)) if nets else Decimal(0)


def amplada_mensual(nets):
    """Meitat del rang interquartílic dels nets mensuals (0 si n'hi ha menys de dos)."""
    if len(nets) < 2:
        return Decimal(0)
    q1, _, q3 = statistics.quantiles(nets, n=4, method="inclusive")
    return (Decimal(q3) - Decimal(q1)) / 2


def resta_mensual(moviments, recurrents, data_referencia, mesos):
    """
    Net de cada mes dels moviments que no són de cap recurrent, en els darrers `mesos` mesos
    complets abans del de data_referencia (només els mesos des que hi ha dades), del més antic
    al més recent.
    """
    if not moviments:
        return []
    dels_recurrents = {id(m) for r in recurrents for m in r.moviments}
    primer_mes = _mes(min(m.data for m in moviments))
    inici_mes_actual = data_referencia.replace(day=1)
    mesos_historic = [_mes(sumar_mesos(inici_mes_actual, -i)) for i in range(1, mesos + 1)]
    mesos_historic = sorted(mes for mes in mesos_historic if mes >= primer_mes)

    net = dict.fromkeys(mesos_historic, Decimal(0))
    for m in moviments:
        if _mes(m.data) in net and id(m) not in dels_recurrents:
            net[_mes(m.data)] += m.import_
    return list(net.values())


def preveure(moviments, criteris_despeses, criteris_ingressos, config, suposits=(), fixos_acabats=()):
    """
    Previsió del saldo total (sense els bancs exclosos) des del darrer moviment fins a
    horitzo_mesos després: els ingressos i despeses fixos actius es repeteixen amb el seu
    interval, i cada mes s'hi suma la despesa variable (mediana mensual de la resta).
    També es calcula la previsió amb els supòsits (moviments nous i fixos que s'acaben), per
    comparar-les, i l'amplada mensual per al rang probable.
    """
    suposits, fixos_acabats = tuple(suposits), tuple(fixos_acabats)
    moviments = [m for m in moviments if m.banc not in config.bancs_exclosos]
    if not moviments:
        return Previsio(None, Decimal(0), Decimal(0), (), (), (), (), suposits, Decimal(0), fixos_acabats)

    data_inici = max(m.data for m in moviments)
    data_fi = sumar_mesos(data_inici, config.horitzo_mesos)
    ingressos = [r for r in detectar_recurrents(moviments, criteris_ingressos, data_inici, ingressos=True)
                 if r.activa]
    despeses = [r for r in detectar_recurrents(moviments, criteris_despeses, data_inici) if r.activa]
    nets = resta_mensual([m for m in moviments if m.categoria not in config.categories_excloses],
                         ingressos + despeses, data_inici, config.mesos_historic)
    variable = Decimal(statistics.median(nets)) if nets else Decimal(0)

    def futurs(acabats=()):
        # El mateix dia, primer els fixos (l'ordenació és estable)
        return (moviments_fixos_previstos(ingressos, 1, data_inici, data_fi, acabats)
                + moviments_fixos_previstos(despeses, -1, data_inici, data_fi, acabats)
                + [(sumar_mesos(data_inici, k), CONCEPTE_VARIABLE, variable)
                   for k in range(1, config.horitzo_mesos + 1)])

    saldo_inicial = saldo_actual(moviments)
    base = _acumular(saldo_inicial, futurs())
    amb_suposits = base
    if suposits or fixos_acabats:
        amb_suposits = _acumular(saldo_inicial, futurs(fixos_acabats)
                                 + moviments_suposits(suposits, data_inici, data_fi))
    return Previsio(data_inici, saldo_inicial, variable, tuple(ingressos), tuple(despeses), base,
                    amb_suposits, suposits, amplada_mensual(nets), fixos_acabats, tuple(config.categories_excloses))
