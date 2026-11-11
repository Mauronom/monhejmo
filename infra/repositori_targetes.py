from datetime import datetime
from decimal import Decimal
from pathlib import Path
from domain import Moviment, FontMoviments

MARCA_TARGETA = "_targeta"
CAPCALERA_MOVIMENTS = "Fecha operación"
# Les retirades de caixer amb la targeta ja surten al compte com a moviment propi
CONCEPTES_IGNORATS = ("REINTEGRO",)


def _llegir_files_xls(path):
    import xlrd
    full = xlrd.open_workbook(str(path)).sheet_by_index(0)
    return [full.row_values(r) for r in range(full.nrows)]


def _import(text):
    """De "-1.203,50" a Decimal("-1203.50")."""
    return Decimal(str(text).strip().replace(".", "").replace(",", "."))


class RepositoriTargetesXls(FontMoviments):
    """
    Compres de targeta dels extractes .xls d'Unicaja, als fitxers <banc>_targeta_<el que sigui>.xls
    del directori. El banc dels moviments és "<banc>_targeta"; el concepte, el nom del comerç; el
    saldo, 0. Una compra que surt en diversos extractes del mateix banc es compta un sol cop.
    """

    def __init__(self, llegir_files=_llegir_files_xls):
        self._llegir_files = llegir_files

    def llegir(self, directori):
        vistos, moviments = set(), []
        for path in sorted(Path(directori).glob(f"*{MARCA_TARGETA}*.xls")):
            banc = path.name.split(MARCA_TARGETA)[0] + MARCA_TARGETA
            for data, hora, comerc, import_ in self._compres(path):
                clau = (banc, data, hora, comerc, import_)
                if clau not in vistos:
                    vistos.add(clau)
                    moviments.append(Moviment(data, comerc, import_, 0, banc))
        return sorted(moviments, key=lambda m: m.data)

    def _compres(self, path):
        files = self._llegir_files(path)
        inici = next((i + 1 for i, fila in enumerate(files) if str(fila[0]).strip() == CAPCALERA_MOVIMENTS), len(files))
        for data, hora, comerc, concepte, import_, *_ in files[inici:]:
            if not str(data).strip() or any(c in str(concepte).upper() for c in CONCEPTES_IGNORATS):
                continue
            yield (datetime.strptime(str(data).strip(), "%d/%m/%Y").date(), str(hora).strip(),
                   str(comerc).strip(), _import(import_))
