from collections import defaultdict
from decimal import Decimal
from .moviment import Moviment

# Concepte de la part dels càrrecs de la targeta al compte que ja està desglossada en compres.
# Conté "credito tarjeta" perquè caigui a la mateixa categoria que els càrrecs.
CONCEPTE_TARGETA_ASSIGNADA = "CREDITO TARJETA ASSIGNADA"


def moviments_assignats_targeta(compres):
    """
    Les compres d'una targeta ja es paguen amb els càrrecs (agregats) que fa al compte. Perquè no es
    comptin dues vegades, per a cada banc de targeta i dia es crea un moviment positiu
    CONCEPTE_TARGETA_ASSIGNADA amb el total de les compres (menys les devolucions), que treu aquesta
    part de la categoria dels càrrecs. Saldo 0: els saldos dels bancs no canvien.
    """
    totals = defaultdict(lambda: Decimal(0))
    for m in compres:
        totals[(m.data, m.banc)] -= m.import_
    return [Moviment(data, CONCEPTE_TARGETA_ASSIGNADA, total, 0, banc)
            for (data, banc), total in sorted(totals.items()) if total != 0]
