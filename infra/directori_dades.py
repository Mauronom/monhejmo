import os
from pathlib import Path

VARIABLE_ENTORN = "COMPTES2_DADES"
DIRECTORI_ANTIC = Path(__file__).resolve().parent / "dades"


def resoldre_directori_dades(env=None, home=None, antic=DIRECTORI_ANTIC):
    """
    Retorna el directori on hi ha les dades de l'usuari (extractes, config.json, categories.json):

    1. La variable d'entorn COMPTES2_DADES, si està definida.
    2. ~/.comptes2, si existeix.
    3. infra/dades dins del projecte, si existeix (ubicació antiga).
    4. Si no hi ha res, crea i fa servir ~/.comptes2.
    """
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)

    if env.get(VARIABLE_ENTORN):
        return Path(env[VARIABLE_ENTORN]).expanduser()

    per_defecte = home / ".comptes2"
    if per_defecte.is_dir():
        return per_defecte
    if antic is not None and Path(antic).is_dir():
        return Path(antic)

    per_defecte.mkdir(parents=True, exist_ok=True)
    return per_defecte
