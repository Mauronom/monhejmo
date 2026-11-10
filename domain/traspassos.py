CATEGORIA_TRASPAS = "traspas"
DIES_MAXIMS_TRASPAS = 5


def _es_transferencia(moviment):
    return "transf" in moviment.concepte.lower()


def marcar_traspassos(moviments, dies=DIES_MAXIMS_TRASPAS):
    """
    Marca com a CATEGORIA_TRASPAS els parells de transferències entre comptes propis: una que surt
    d'un banc i una altra del mateix import que entra en un altre banc com a molt `dies` dies
    després o abans. Cada moviment fa parella com a molt una vegada, amb el més proper en el temps.
    Tots dos conceptes han de ser transferències ("transf"), perquè els moviments ficticis
    (SIALP, efectiu) també tenen parelles exactes i no són traspassos.
    Retorna còpies en el mateix ordre; no modifica els originals.
    """
    copies = [m.clone() for m in moviments]
    entrades = [m for m in copies if m.import_ > 0 and _es_transferencia(m)]
    aparellades = set()
    for sortida in sorted((m for m in copies if m.import_ < 0 and _es_transferencia(m)), key=lambda m: m.data):
        candidates = [e for e in entrades
                      if id(e) not in aparellades and e.banc != sortida.banc and e.import_ == -sortida.import_
                      and abs((e.data - sortida.data).days) <= dies]
        if candidates:
            entrada = min(candidates, key=lambda e: abs((e.data - sortida.data).days))
            aparellades.add(id(entrada))
            sortida.categoria = entrada.categoria = CATEGORIA_TRASPAS
    return copies
