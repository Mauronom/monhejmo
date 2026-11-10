import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple

DIES_PER_MES = Decimal("30.44")
CENTIMS = Decimal("0.01")
MARGE_IMPORT_SEMBLANT = Decimal("1.10")


@dataclass(frozen=True)
class CriterisRecurrents:
    """
    Com es decideix què és una despesa (o un ingrés) fix.
    - min_mesos: mesos diferents en què s'ha de cobrar com a mínim.
    - max_carrecs_per_mes: càrrecs per mes (de mitjana) com a màxim; més vol dir moviments del dia a dia.
    - max_variacio: desviació típica / mitjana dels imports com a màxim.
    - incloure: textos de concepte que sempre són fixos, encara que no passin els criteris.
    - excloure: textos de concepte que mai no són fixos (guanya sobre incloure).
    Els textos no distingeixen majúscules.
    """
    min_mesos: int = 4
    max_carrecs_per_mes: float = 1.5
    max_variacio: float = 0.5
    incloure: Tuple[str, ...] = ()
    excloure: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MovimentRecurrent:
    """Una despesa o un ingrés que es repeteix. Els imports són sempre positius."""
    concepte: str             # el del darrer càrrec
    banc: str
    categoria: str            # la del darrer càrrec
    carrecs: int
    import_habitual: Decimal  # mitjana dels càrrecs
    import_mensual: Decimal   # import habitual repartit per mes segons la periodicitat
    periodicitat: str
    primera: date
    darrera: date
    activa: bool              # si es continua cobrant a la data de referència
    interval_dies: Decimal = Decimal(30)  # dies entre càrrecs, de mitjana
    moviments: Tuple = field(default=(), compare=False, repr=False)  # els càrrecs, tal com són


def clau_concepte(concepte):
    """Concepte normalitzat per agrupar càrrecs: minúscules, sense números ni signes."""
    text = re.sub(r"\d+", "", concepte.lower())
    text = re.sub(r"[^\w\s]|_", " ", text)
    return " ".join(text.split())


def _conte_algun(concepte, textos):
    concepte = concepte.lower()
    return any(t.lower() in concepte for t in textos)


def _periodicitat(interval_dies):
    for limit, nom in ((10, "setmanal"), (25, "més d'un cop al mes"), (45, "mensual"), (75, "bimestral"),
                       (120, "trimestral"), (240, "semestral")):
        if interval_dies <= limit:
            return nom
    return "anual"


def _mesos(carrecs):
    return len({(m.data.year, m.data.month) for m in carrecs})


def _separar_per_import(carrecs):
    """Agrupa els càrrecs d'imports semblants (fins a un 10% més que el primer del grup)."""
    grups = []
    for m in sorted(carrecs, key=lambda m: -m.import_):
        if grups and -m.import_ <= -grups[-1][0].import_ * MARGE_IMPORT_SEMBLANT:
            grups[-1].append(m)
        else:
            grups.append([m])
    return grups


def _rebuts(carrecs, criteris):
    """
    Si un concepte es cobra més cops dels que toca per mes, sol ser que hi ha diversos rebuts amb
    el mateix concepte (p. ex. la quota i una derrama): se separen per import i es descarten els
    càrrecs puntuals (els grups de menys de min_mesos càrrecs). Només si es cobren els mateixos
    dies; si no, és despesa del dia a dia (p. ex. liquidacions de targeta) i es deixa sencera
    perquè no passi la detecció. Si en separar no en queda cap, també es deixa sencera.
    """
    mesos = _mesos(carrecs)
    dies_de_cobrament = len({m.data for m in carrecs})
    if (len(carrecs) / mesos <= criteris.max_carrecs_per_mes
            or dies_de_cobrament / mesos > criteris.max_carrecs_per_mes):
        return [carrecs]
    rebuts = [grup for grup in _separar_per_import(carrecs) if len(grup) >= criteris.min_mesos]
    return rebuts or [carrecs]


MIN_PARAULES_CONCEPTE_TALLAT = 3


def _ajuntar_conceptes_tallats(grups):
    """
    El banc de vegades talla el mateix concepte de maneres diferents (p. ex. "BIZUM A: NOM COGNOM
    Cog" i "BIZUM A: NOM COGNOM"). Dins d'un mateix banc, un concepte que és un altre més una sola
    paraula al final s'ajunta amb el més curt, si aquest té com a mínim MIN_PARAULES_CONCEPTE_TALLAT
    paraules (perquè no s'ajuntin conceptes genèrics).
    """
    resultat = defaultdict(list)
    for (banc, clau), carrecs in grups.items():
        paraules = clau.split()
        curta = " ".join(paraules[:-1])
        if len(paraules) > MIN_PARAULES_CONCEPTE_TALLAT and (banc, curta) in grups:
            resultat[(banc, curta)].extend(carrecs)
        else:
            resultat[(banc, clau)].extend(carrecs)
    return resultat


def _es_regular(carrecs, criteris):
    mesos = _mesos(carrecs)
    if mesos < criteris.min_mesos or len(carrecs) / mesos > criteris.max_carrecs_per_mes:
        return False
    imports = [float(-m.import_) for m in carrecs]
    return statistics.pstdev(imports) / statistics.mean(imports) <= criteris.max_variacio


FACTOR_SALT = 3


def _carrecs_recents(carrecs):
    """
    Els càrrecs posteriors al darrer salt (un interval més de FACTOR_SALT vegades la mediana), que
    són els que reflecteixen com es cobra ara (p. ex. una primera visita i, mesos després, una quota
    mensual). Si després del salt només hi ha un càrrec, tots.
    """
    intervals = [(b.data - a.data).days for a, b in zip(carrecs, carrecs[1:])]
    if len(intervals) < 2:
        return carrecs
    limit = FACTOR_SALT * statistics.median(intervals)
    salts = [i for i, dies in enumerate(intervals) if dies > limit]
    if salts and len(carrecs) - (salts[-1] + 1) >= 2:
        return carrecs[salts[-1] + 1:]
    return carrecs


def _recurrent(carrecs, data_referencia, originals):
    carrecs = sorted(carrecs, key=lambda m: m.data)
    primer, darrer = carrecs[0], carrecs[-1]
    n = len(carrecs)
    recents = _carrecs_recents(carrecs)
    interval = max(Decimal((darrer.data - recents[0].data).days) / (len(recents) - 1), Decimal(1))
    import_habitual = -sum((m.import_ for m in recents), Decimal(0)) / len(recents)
    return MovimentRecurrent(
        concepte=darrer.concepte,
        banc=darrer.banc,
        categoria=darrer.categoria,
        carrecs=n,
        import_habitual=import_habitual.quantize(CENTIMS, ROUND_HALF_UP),
        import_mensual=(import_habitual * DIES_PER_MES / interval).quantize(CENTIMS, ROUND_HALF_UP),
        periodicitat=_periodicitat(interval),
        primera=primer.data,
        darrera=darrer.data,
        activa=(data_referencia - darrer.data).days <= interval * Decimal("1.5") + 10,
        interval_dies=interval,
        moviments=tuple(originals.get(id(m), m) for m in carrecs),
    )


def detectar_recurrents(moviments, criteris, data_referencia: Optional[date] = None, ingressos=False):
    """
    Busca les despeses (o, amb ingressos=True, els ingressos) que es repeteixen (mateix banc i
    concepte llevat dels números) amb una regularitat i un import semblants. Un mateix concepte pot
    donar diversos rebuts (vegeu _rebuts). data_referencia (per defecte, la del darrer moviment)
    decideix si encara s'estan cobrant. Retorna primer els actius, de més a menys import mensual.
    """
    moviments = list(moviments)
    if not moviments:
        return []
    data_referencia = data_referencia or max(m.data for m in moviments)
    originals = {}  # id de la còpia amb el signe girat -> moviment original
    if ingressos:
        # Amb el signe girat, els ingressos es tracten exactament igual que les despeses
        girats = [replace(m, import_=-m.import_) for m in moviments]
        originals = {id(g): m for g, m in zip(girats, moviments)}
        moviments = girats

    grups = defaultdict(list)
    for m in moviments:
        if m.import_ < 0 and not _conte_algun(m.concepte, criteris.excloure):
            grups[(m.banc, clau_concepte(m.concepte))].append(m)
    grups = _ajuntar_conceptes_tallats(grups)

    recurrents = [_recurrent(rebut, data_referencia, originals)
                  for carrecs in grups.values()
                  for rebut in _rebuts(carrecs, criteris)
                  if len(rebut) > 1  # un sol càrrec no es repeteix, encara que s'inclogui
                  and (any(_conte_algun(m.concepte, criteris.incloure) for m in rebut)
                       or _es_regular(rebut, criteris))]
    return sorted(recurrents, key=lambda d: (not d.activa, -d.import_mensual, d.concepte))


def import_mensual_total(recurrents):
    """Import mensual dels que encara s'estan cobrant."""
    return sum((d.import_mensual for d in recurrents if d.activa), Decimal(0))
