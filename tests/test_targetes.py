from datetime import date
from decimal import Decimal
from domain import Moviment, moviments_assignats_targeta, CONCEPTE_TARGETA_ASSIGNADA
from infra import RepositoriTargetesXls


def _compra(data, concepte, import_, banc="banc_targeta"):
    return Moviment(data, concepte, Decimal(import_), 0, banc)


def test_un_moviment_assignat_per_banc_i_dia_amb_la_suma_de_les_compres():
    compres = [_compra(date(2026, 5, 4), "FORN", "-3.50"),
               _compra(date(2026, 5, 4), "SUPERMERCAT", "-20.25"),
               _compra(date(2026, 5, 4), "LLIBRERIA", "-12", banc="altre_targeta"),
               _compra(date(2026, 5, 6), "FARMACIA", "-8")]

    assignats = moviments_assignats_targeta(compres)

    assert [(m.data, m.concepte, m.import_, m.balance, m.banc) for m in assignats] == [
        (date(2026, 5, 4), CONCEPTE_TARGETA_ASSIGNADA, Decimal("12"), 0, "altre_targeta"),
        (date(2026, 5, 4), CONCEPTE_TARGETA_ASSIGNADA, Decimal("23.75"), 0, "banc_targeta"),
        (date(2026, 5, 6), CONCEPTE_TARGETA_ASSIGNADA, Decimal("8"), 0, "banc_targeta")]


def test_les_devolucions_resten_del_dia():
    compres = [_compra(date(2026, 5, 4), "BOTIGA", "-30"), _compra(date(2026, 5, 4), "BOTIGA", "10")]

    assert [m.import_ for m in moviments_assignats_targeta(compres)] == [Decimal(20)]


def test_un_dia_amb_compres_i_devolucions_que_s_anul_len_no_te_moviment():
    compres = [_compra(date(2026, 5, 4), "BOTIGA", "-30"), _compra(date(2026, 5, 4), "BOTIGA", "30")]

    assert moviments_assignats_targeta(compres) == []


# --- Lector dels extractes .xls ---------------------------------------------

CAPCALERA = [["", "", "", "", "", ""],
             ["Movimientos de tarjeta", "", "", "", "", ""],
             ["Titular:", "PERSONA INVENTADA", "", "Fecha desde:", "01/05/2026", ""],
             ["", "", "", "", "", ""],
             ["Fecha operación", "Hora", "Nombre comercio", "Concepto", "Importe", "Divisa"]]


def _repositori(tmp_path, files_per_fitxer):
    for nom in files_per_fitxer:
        (tmp_path / nom).write_bytes(b"")
    return RepositoriTargetesXls(llegir_files=lambda path: CAPCALERA + files_per_fitxer[path.name])


def test_llegeix_les_compres_dels_fitxers_de_targeta(tmp_path):
    repositori = _repositori(tmp_path, {"unicaja_targeta_1.xls": [
        ["09/05/2026", "18:23", "SUPERMERCAT DEL BARRI", "COMPRA", "-8,75", "EUR"],
        ["08/05/2026", "11:49", "FORN DE PA", "COMPRA", "-1.203,50", "EUR"],
        ["07/05/2026", "10:00", "BOTIGA", "DEVOLUCION", "12,00", "EUR"]]})

    moviments = repositori.llegir(tmp_path)

    assert [(m.data, m.concepte, m.import_, m.balance, m.banc) for m in moviments] == [
        (date(2026, 5, 7), "BOTIGA", Decimal("12.00"), 0, "unicaja_targeta"),
        (date(2026, 5, 8), "FORN DE PA", Decimal("-1203.50"), 0, "unicaja_targeta"),
        (date(2026, 5, 9), "SUPERMERCAT DEL BARRI", Decimal("-8.75"), 0, "unicaja_targeta")]


def test_no_llegeix_les_retirades_de_caixer_que_ja_son_al_compte(tmp_path):
    repositori = _repositori(tmp_path, {"unicaja_targeta_1.xls": [
        ["09/05/2026", "13:24", "UN ALTRE BANC", "REINTEGRO EN CAJERO", "-400,00", "EUR"],
        ["09/05/2026", "18:23", "FORN DE PA", "COMPRA", "-3,50", "EUR"]]})

    assert [m.concepte for m in repositori.llegir(tmp_path)] == ["FORN DE PA"]


def test_les_compres_repetides_en_dos_extractes_de_la_mateixa_targeta_es_compten_un_cop(tmp_path):
    forn = ["09/05/2026", "18:23", "FORN DE PA", "COMPRA", "-3,50", "EUR"]
    repositori = _repositori(tmp_path, {
        "unicaja_targeta_1.xls": [forn],
        "unicaja_targeta_2.xls": [forn, ["10/05/2026", "09:00", "FARMACIA", "COMPRA", "-8,00", "EUR"]],
        "banc_targeta_x.xls": [forn]})

    moviments = repositori.llegir(tmp_path)

    assert sorted((m.banc, m.concepte) for m in moviments) == [
        ("banc_targeta", "FORN DE PA"), ("unicaja_targeta", "FARMACIA"), ("unicaja_targeta", "FORN DE PA")]


def test_nomes_llegeix_els_fitxers_amb_el_nom_de_targeta(tmp_path):
    (tmp_path / "unicaja.n43").write_text("")
    (tmp_path / "altres.xls").write_bytes(b"")

    assert RepositoriTargetesXls(llegir_files=lambda path: 1 / 0).llegir(tmp_path) == []
