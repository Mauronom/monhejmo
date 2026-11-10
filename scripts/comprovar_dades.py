#!/usr/bin/env python3
"""
Xarxa de seguretat per als refactors: carrega les dades reals sense interfície
i calcula una "empremta" del resultat (moviments, estadístiques, categories, gràfiques).

    python3 scripts/comprovar_dades.py --desar   # guarda l'empremta de referència
    python3 scripts/comprovar_dades.py           # compara amb la referència

La referència es guarda al directori de dades (conté imports reals, no va a git).
Quan canviï l'API dels casos d'ús, s'adapta la funció `calcular_empremta`,
però la referència desada no es toca: el resultat ha de continuar sent el mateix.
"""
import argparse
import hashlib
import json
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import (CarregarMoviments, FiltrarMoviments, MovimentsSessio,
                 GraficaBalance, GraficaImports, GraficaCategories)
from domain import FiltreMoviments
from infra.ui_bokeh import hores_dels_punts
from infra import (RepositoriMovimentsNorma43, RepositoriCategoria,
                   JsonConfigMovimentsFicticisRepo, resoldre_directori_dades)


def _stats(resum):
    """Com es mostren a la interfície: total sense arrodonir, diari i mensual a 2 decimals."""
    return (resum.total, round(resum.diari, 2), round(resum.mensual, 2))


def _norm(valor):
    """Converteix a una forma comparable i serialitzable (Decimal normalitzat, dates en ISO)."""
    if isinstance(valor, Decimal):
        return str(valor.normalize()) if valor != 0 else "0"
    if isinstance(valor, float):
        return _norm(Decimal(str(valor)))
    if isinstance(valor, (list, tuple)):
        return [_norm(v) for v in valor]
    if isinstance(valor, dict):
        return {str(k): _norm(v) for k, v in sorted(valor.items())}
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    return valor


def _hash(valor):
    return hashlib.sha256(json.dumps(_norm(valor), ensure_ascii=False).encode()).hexdigest()[:16]


def _punts_amb_hora(punts):
    """Els punts tal com es dibuixen: (hora, saldo, banc, concepte, import)."""
    return [(h, p.saldo, p.banc, p.concepte, p.import_) for p, h in zip(punts, hores_dels_punts(punts))]


def calcular_empremta(directori):
    sessio = MovimentsSessio()
    carregar = CarregarMoviments(RepositoriMovimentsNorma43(),
                                 JsonConfigMovimentsFicticisRepo(directori / "config.json"),
                                 RepositoriCategoria(directori), sessio)

    resultat = carregar.execute(directori)
    moviments = resultat.moviments
    files = [(m.data, m.concepte, m.import_, m.balance, m.banc, m.categoria) for m in moviments]

    per_categoria = defaultdict(lambda: Decimal(0))
    per_banc = defaultdict(int)
    for m in moviments:
        per_categoria[m.categoria] += m.import_
        per_banc[m.banc] += 1

    # Un filtre representatiu: l'últim mes amb dades
    ultima = max(m.data for m in moviments)
    filtrat = FiltrarMoviments(sessio).execute(FiltreMoviments(data_inici=ultima.replace(day=1), data_fi=ultima))

    return {
        "moviments": len(moviments),
        "moviments_hash": _hash(files),
        "stats": _norm(_stats(resultat.resum)),
        "per_banc": _norm(dict(per_banc)),
        "per_categoria": _norm(dict(per_categoria)),
        "grafica_balance_hash": _hash(_punts_amb_hora(GraficaBalance(sessio).execute(FiltreMoviments())["punts"])),
        "grafica_imports_hash": _hash(_punts_amb_hora(GraficaImports(sessio).execute(FiltreMoviments())["punts"])),
        "grafica_categories": _norm(GraficaCategories(sessio).execute(FiltreMoviments())),
        "filtre_ultim_mes": {"moviments": len(filtrat.moviments), "stats": _norm(_stats(filtrat.resum))},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--desar", action="store_true", help="desa l'empremta actual com a referència")
    args = parser.parse_args()

    directori = resoldre_directori_dades()
    referencia_path = directori / "empremta_referencia.json"
    actual = calcular_empremta(directori)

    if args.desar:
        referencia_path.write_text(json.dumps(actual, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Referència desada a {referencia_path} ({actual['moviments']} moviments)")
        return 0

    if not referencia_path.exists():
        print(f"No hi ha referència a {referencia_path}. Executa primer amb --desar.")
        return 2

    referencia = json.loads(referencia_path.read_text(encoding="utf-8"))
    diferencies = [k for k in sorted(set(referencia) | set(actual)) if referencia.get(k) != actual.get(k)]
    if not diferencies:
        print(f"OK: el resultat coincideix amb la referència ({actual['moviments']} moviments)")
        return 0

    print("DIFERENT de la referència:")
    for k in diferencies:
        print(f"  {k}:\n    referència: {referencia.get(k)}\n    actual:     {actual.get(k)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
