from .moviment import Moviment


def generar_moviments_ficticis(moviments, regles, inicials):
    """
    Retorna els moviments ficticis: una còpia dels inicials i, per a cada moviment que
    coincideix amb una regla (la primera que coincideixi), un moviment al banc de destí.
    El saldo de cada moviment generat és el saldo acumulat del seu banc de destí,
    partint del moviment inicial d'aquell banc (o de 0 si no en té).
    """
    ficticis = Moviment.clone_list(inicials)
    saldos = {m.banc: m.balance for m in ficticis}

    for m in moviments:
        regla = next((r for r in regles if any(patro in m.concepte for patro in r.patrons)), None)
        if regla is None:
            continue
        import_ = -m.import_ if regla.invertir_import else m.import_
        saldo = saldos.get(regla.banc_desti, 0) + import_
        saldos[regla.banc_desti] = saldo
        ficticis.append(Moviment(
            data=m.data,
            concepte=regla.concepte_desti,
            import_=import_,
            balance=saldo,
            banc=regla.banc_desti,
        ))

    return ficticis
