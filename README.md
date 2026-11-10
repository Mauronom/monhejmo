# monhejmo

Aplicació d'escriptori per entendre les finances de casa a partir dels extractes bancaris en format
**Norma 43** (`.n43`), el que fan servir la majoria de bancs espanyols per descarregar els moviments.

Totes les dades es queden al teu ordinador: l'aplicació no es connecta a cap banc ni a cap servei.

## Què fa

- **Moviments**: llegeix tots els extractes d'un directori (un fitxer per banc) i els mostra en una
  taula amb el saldo de cada banc i el saldo total de tots els comptes. Es poden filtrar per text,
  dates i categoria.
- **Categories**: assigna una categoria a cada moviment segons paraules del concepte, i es poden
  afegir, editar i eliminar des de l'aplicació.
- **Traspassos**: detecta les transferències entre els teus propis comptes (mateix import, signe
  contrari, bancs diferents i pocs dies de diferència) perquè no comptin com a despesa ni ingrés.
- **Gràfiques** (Bokeh, al navegador): evolució del saldo per banc i total, imports acumulats i
  despesa per categoria.
- **Despeses i ingressos fixos**: detecta els càrrecs i els cobraments que es repeteixen (rebuts,
  nòmines, quotes...), amb la periodicitat i el cost o l'ingrés mensual.
- **Previsió**: estima el saldo total dels propers mesos a partir dels fixos i de la resta de
  moviments habituals (mediana mensual), amb un rang probable que s'eixampla amb el temps. S'hi poden
  afegir supòsits (una despesa o un ingrés nou, puntual o periòdic) i indicar fixos que s'acaben.
- **Pagaments en efectiu**: permet declarar pagaments fixos que es fan amb diners del caixer (p. ex.
  la neteja de casa) perquè surtin com a despesa amb la seva categoria i no només com a "efectiu".

## Instal·lació

Cal Python 3.10 o més nou.

```bash
git clone https://github.com/Mauronom/monhejmo.git
cd monhejmo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ús

```bash
python3 main.py
```

En obrir-se, l'aplicació proposa el directori de dades i, en acceptar, llegeix tots els `.n43` que hi
ha. El nom de cada fitxer (sense l'extensió) és el nom del banc: `banc_a.n43`, `banc_b.n43`...

### Directori de dades

Les dades (extractes, categories i configuració) es busquen per aquest ordre:

1. El directori de la variable d'entorn `COMPTES2_DADES`, si està definida.
2. `~/.comptes2`, si existeix.
3. Si no hi ha res, es crea `~/.comptes2`.

```text
~/.comptes2/
├── banc_a.n43
├── banc_b.n43
├── categories.json
└── config.json
```

### Categories

`categories.json` relaciona cada categoria amb les paraules que la identifiquen al concepte (sense
distingir majúscules). Pots començar copiant l'exemple:

```bash
mkdir -p ~/.comptes2
cp exemples/categories.json ~/.comptes2/
```

```json
{
  "alimentacio": ["supermercat", "fruiteria"],
  "efectiu": ["cajero", "retirada efectivo"]
}
```

Després les pots gestionar des del botó "Gestionar Categories".

### Configuració (`config.json`)

És opcional: totes les seccions tenen valors per defecte. Els supòsits, els fixos que s'acaben i els
pagaments en efectiu es poden afegir des de l'aplicació, que els desa en aquest fitxer.

```json
{
  "despeses_fixes": {
    "min_mesos": 4,
    "max_carrecs_per_mes": 1.5,
    "max_variacio": 0.5,
    "incloure": ["comunitat"],
    "excloure": ["cafeteria"]
  },
  "ingressos_fixos": {
    "excloure": ["bizum"]
  },
  "previsio": {
    "horitzo_mesos": 12,
    "mesos_historic": 12,
    "bancs_exclosos": [],
    "categories_excloses": ["obres"]
  },
  "moviments_ficticis": {
    "pla_estalvi": {
      "patrons": ["APORTACIO PLA ESTALVI"],
      "concepte_desti": "PLA ESTALVI",
      "banc_desti": "ESTALVI"
    }
  },
  "moviments_inicials": [
    {"data": "2024-01-01", "concepte": "PLA ESTALVI", "import": 0, "balance": 5000, "banc": "ESTALVI"}
  ]
}
```

- **`despeses_fixes` / `ingressos_fixos`**: quan es considera fix un moviment. Ha d'aparèixer en
  `min_mesos` mesos diferents, amb `max_carrecs_per_mes` càrrecs per mes com a màxim i una variació de
  l'import (desviació típica / mitjana) de `max_variacio` com a màxim. Els conceptes que contenen un
  text d'`incloure` sempre són fixos, i els d'`excloure` no ho són mai.
- **`previsio`**: quants mesos endavant es preveu, quants mesos enrere es miren, bancs que no compten
  (p. ex. productes d'estalvi) i categories de despeses puntuals que no s'han de repetir a la previsió.
- **`moviments_ficticis`** i **`moviments_inicials`**: per seguir comptes que no tenen extracte (p.
  ex. un pla d'estalvi). Cada moviment del banc que coincideix amb un dels `patrons` genera el moviment
  contrari al banc `banc_desti`, que comença amb el saldo dels `moviments_inicials`.

## Estructura

El codi segueix una arquitectura hexagonal:

- `domain/`: entitats i regles de negoci pures (moviments, categories, fixos, previsió...), sense
  dependències externes. Els imports es calculen amb `Decimal`.
- `app/`: casos d'ús que fa servir la interfície (`CasosUs`).
- `infra/`: adaptadors: lectura de Norma 43, repositoris JSON, interfície amb FreeSimpleGUI i gràfiques
  amb Bokeh.
- `tests/`: proves amb pytest.
- `scripts/`: `comprovar_dades.py` desa una empremta dels resultats amb les teves dades i avisa si un
  canvi de codi els altera; `comprovacio_manual.md` és la llista de comprovacions de la interfície.

## Tests

```bash
python3 -m pytest
```
