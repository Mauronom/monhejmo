from datetime import datetime
from decimal import Decimal
from decimal import InvalidOperation
from domain import (CATEGORIA_PER_DEFECTE, CategoriaInvalida, FiltreMoviments, parsejar_paraules_clau,
                    PERIODICITATS, Suposit, SupositInvalid, FixAcabat, PagamentEfectiu)

TOTES = "Totes"  # Opció del desplegable que vol dir "sense filtre de categoria"


def llegir_data(text):
    """Converteix "AAAA-MM-DD" en date. Retorna None si és buit o no és una data vàlida."""
    text = (text or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def construir_filtre(text, data_inici, data_fi, categoria):
    """Construeix el filtre a partir dels valors dels camps de la finestra."""
    return FiltreMoviments(
        text=text or "",
        data_inici=llegir_data(data_inici),
        data_fi=llegir_data(data_fi),
        categoria=None if categoria in (None, "", TOTES) else categoria,
    )


def files_recurrents(despeses):
    """Files de la taula de despeses fixes."""
    return [[d.concepte, d.banc, d.categoria, d.periodicitat, f"{d.import_habitual:.2f}",
             f"{d.import_mensual:.2f}", d.carrecs, str(d.primera), str(d.darrera),
             "actiu" if d.activa else "acabat"] for d in despeses]


def files_despeses_categoria(despeses):
    """Files de la taula de despeses variables per categoria, amb el percentatge sobre el total."""
    def percentatge(c):
        return f"{c.total * 100 / despeses.total:.1f} %" if despeses.total else ""
    return [[c.categoria, f"{c.total:.2f}", f"{c.mensual:.2f}", c.moviments, percentatge(c)]
            for c in despeses.per_categoria]


def files_despeses_puntuals(despeses):
    """Files de la taula de despeses puntuals grosses (l'import en positiu)."""
    return [[str(m.data), m.concepte, m.banc, m.categoria, f"{-m.import_:.2f}"] for m in despeses.puntuals]


def text_resum_despeses_variables(despeses):
    return (f"Total: {despeses.total:.2f} € en {despeses.mesos:.2f} mesos ({despeses.mensual:.2f} €/mes). "
            f"Puntuals a part: {despeses.total_puntuals:.2f} €.")


def text_resum_previsio(resultat):
    """Text del resum de la previsió: d'on es parteix i el saldo previst."""
    previsio = resultat.previsio
    ingressos = sum((r.import_mensual for r in previsio.ingressos_fixos), Decimal(0))
    despeses = sum((r.import_mensual for r in previsio.despeses_fixes), Decimal(0))
    saldo_actual = f"Saldo actual ({previsio.data_inici}): {previsio.saldo_inicial:.2f} €"
    sense_categories = f", sense {', '.join(previsio.categories_excloses)}" if previsio.categories_excloses else ""
    if resultat.saldos_exclosos:
        exclosos = ", ".join(f"{banc}: {saldo:.2f} €" for banc, saldo in resultat.saldos_exclosos.items())
        total = previsio.saldo_inicial + sum(resultat.saldos_exclosos.values(), Decimal(0))
        saldo_actual += f" (sense {exclosos}; total {total:.2f} €)"
    linies = [
        saldo_actual,
        f"Ingressos fixos: +{ingressos:.2f} €/mes",
        f"Despeses fixes: -{despeses:.2f} €/mes",
        f"Resta de moviments (mediana{sense_categories}): {previsio.variable_mensual:.2f} €/mes",
    ]
    if previsio.te_suposits:
        suposits = [f"{s.concepte} ({s.import_:.2f} € {s.periodicitat})" for s in previsio.suposits]
        suposits += [f"{f.concepte} s'acaba el {f.data_fi}" for f in previsio.fixos_acabats]
        linies.append("Inclou els supòsits: " + "; ".join(suposits))
    linies += ["", "Saldo previst (i rang probable):"]
    linies += [f"  d'aquí a {r.mesos} mesos ({r.data}): {r.saldo:.2f} € "
               f"(entre {r.saldo - r.marge:.2f} i {r.saldo + r.marge:.2f})" for r in resultat.resum]
    return "\n".join(linies)


def llegir_pagament_efectiu(concepte, import_, periodicitat, data_inici, data_fi):
    """PagamentEfectiu a partir dels camps del formulari. Llança SupositInvalid si algun camp no és vàlid."""
    s = llegir_suposit(concepte, import_, periodicitat, data_inici, data_fi)
    return PagamentEfectiu(s.concepte, s.import_, s.periodicitat, s.data_inici, s.data_fi)


def files_fixos_acabats(fixos):
    """Files de la taula de fixos que s'acaben."""
    return [[f.concepte, f.banc, str(f.data_fi)] for f in fixos]


def opcions_fixos(previsio):
    """Ingressos i despeses fixos actius per triar quin s'acaba: {etiqueta: (banc, concepte)}."""
    return {f"{tipus} · {r.concepte} ({r.banc}) · {r.import_mensual:.2f} €/mes": (r.banc, r.concepte)
            for tipus, recurrents in (("Ingrés", previsio.ingressos_fixos), ("Despesa", previsio.despeses_fixes))
            for r in recurrents}


def files_suposits(suposits):
    """Files de la taula de supòsits."""
    return [[s.concepte, f"{s.import_:.2f}", s.periodicitat, str(s.data_inici), str(s.data_fi or "")]
            for s in suposits]


def llegir_suposit(concepte, import_, periodicitat, data_inici, data_fi):
    """Suposit a partir dels camps del formulari. Llança SupositInvalid si algun camp no és vàlid."""
    try:
        import_ = Decimal((import_ or "").strip().replace(",", ".").replace("−", "-"))
    except InvalidOperation:
        raise SupositInvalid("L'import ha de ser un número (negatiu si és una despesa).")
    inici = llegir_data(data_inici)
    if inici is None:
        raise SupositInvalid("La data d'inici ha de ser AAAA-MM-DD.")
    fi = llegir_data(data_fi)
    if (data_fi or "").strip() and fi is None:
        raise SupositInvalid("La data de fi ha de ser AAAA-MM-DD o buida.")
    return Suposit((concepte or "").strip(), import_, periodicitat, inici, fi)


def files_moviments(moviments, saldos_totals):
    """Files de les taules de moviments: el balanç del banc i el total de tots els bancs."""
    return [[str(m.data), m.concepte, f"{m.import_:.2f}", m.balance, f"{total:.2f}", m.banc, m.categoria]
            for m, total in zip(moviments, saldos_totals)]


def _data_valida_o_buida(text):
    return not (text or "").strip() or llegir_data(text) is not None


class UIFreeSimpleGUI:
    """UI amb FreeSimpleGUI: taules de moviments, filtres, gràfiques i gestió de categories."""

    def __init__(self, casos_us, ui_grafica, directori_dades="."):
        """casos_us: app.CasosUs. ui_grafica: on es dibuixen les gràfiques (p. ex. UIBokeh)."""
        import FreeSimpleGUI as sg
        self._casos = casos_us
        self._ui_grafica = ui_grafica
        self._directori_dades = str(directori_dades)

        # Definició de la interfície
        sg.set_options(font=('Arial', 20))  # Nom de la font i mida

        layout = [
            [sg.Text("Filtre:"), sg.Input(key="-INPUT_FILTRE-", enable_events=True),
             sg.Text("Categoria:"), sg.Combo(values=[], key="-COMBO_CATEGORIA-", enable_events=True, readonly=True, size=(15, 1))],
            [sg.Text("Data inici:"),
             sg.Input(key="-DATA_INICI-", size=(12, 1), enable_events=True),
             sg.CalendarButton("📅", target="-DATA_INICI-", format="%Y-%m-%d", font=('Arial', 20)),
             sg.Text("Data fi:"),
             sg.Input(key="-DATA_FI-", size=(12, 1), enable_events=True),
             sg.CalendarButton("📅", target="-DATA_FI-", format="%Y-%m-%d", font=('Arial', 20))],
            # Botons agrupats per files perquè hi càpiguen tots encara que la finestra sigui estreta
            [sg.Text("Gràfiques:", size=(13, 1)),
             sg.Button("Balanç", key="-BTN_BALANCE-"),
             sg.Button("Imports", key="-BTN_IMPORTS-"),
             sg.Button("Categories", key="-BTN_CATEGORIES-")],
            [sg.Text("Anàlisi:", size=(13, 1)),
             sg.Button("Despeses fixes", key="-BTN_DESPESES_FIXES-"),
             sg.Button("Ingressos fixos", key="-BTN_INGRESSOS_FIXOS-"),
             sg.Button("Despeses variables", key="-BTN_DESPESES_VARIABLES-"),
             sg.Button("Previsió", key="-BTN_PREVISIO-")],
            [sg.Text("Configuració:", size=(13, 1)),
             sg.Button("Gestionar categories", key="-BTN_GESTIONAR_CATEGORIES-"),
             sg.Button("Pagaments en efectiu", key="-BTN_PAGAMENTS_EFECTIU-")],
            [sg.Table(values=[],
                      headings=["Data", "Concepte", "Import (€)", "Balanç del banc", "Balanç total", "Banc", 'Categoria'],
                      auto_size_columns=True,
                      justification="left",
                      key="-TAULA-",
                      expand_x=True,
                      expand_y=True,
                      enable_events=True,
                      num_rows=8)],
            [sg.Table(values=[],
                      headings=["Data", "Concepte", "Import (€)", "Balanç del banc", "Balanç total", "Banc", 'Categoria'],
                      auto_size_columns=True,
                      justification="left",
                      key="-TAULA2-",
                      expand_x=True,
                      expand_y=True,
                      enable_events=True,
                      num_rows=8)],
            [sg.Text("Total: "), sg.Text("0.00", key="-Total-"),
             sg.Text("Diari: "), sg.Text("0.00", key="-Diari-"),
             sg.Text("Mensual: "), sg.Text("0.00", key="-Mensual-")],
        ]
        self.window = sg.Window("Moviments Bancaris", layout, finalize=True, resizable=True, size=(1200, 700))
        self._finestra_categories_actual = None  # Finestra de categories, mentre està oberta
        self._directori_carregat = None  # D'on s'han carregat els moviments, per tornar-los a carregar
        self.window["-COMBO_CATEGORIA-"].update(values=[TOTES], value=TOTES)
        self._actualitzar_categories()

    # --- Diàlegs -------------------------------------------------------------

    def mostrar_popup(self, titol, text):
        """Mostra un popup amb un títol i un text."""
        import FreeSimpleGUI as sg
        sg.popup(titol, text)

    def input_popup(self, text, title, default_text=None):
        """Mostra un popup per demanar entrada d'usuari."""
        import FreeSimpleGUI as sg
        return sg.popup_get_text(text, title=title, default_text=default_text)

    def confirmar_accio(self, missatge):
        """Mostra un diàleg de confirmació per a l'usuari."""
        import FreeSimpleGUI as sg
        resposta = sg.popup_yes_no(missatge)
        return resposta == "Yes"

    def seleccionar_categoria(self, categories, missatge):
        """Mostra un diàleg per permetre a l'usuari seleccionar una categoria."""
        import FreeSimpleGUI as sg

        if not categories:
            sg.popup("Error", "No hi ha categories disponibles.")
            return None

        layout = [
            [sg.Text(missatge)],
            [sg.Listbox(values=categories, size=(30, 10), key="-SELECTED_CATEGORY-", bind_return_key=True)],
            [sg.Button("Seleccionar"), sg.Button("Cancel·lar")]
        ]

        window = sg.Window("Seleccionar Categoria", layout, modal=True)

        while True:
            event, values = window.read()

            if event == sg.WINDOW_CLOSED or event == "Cancel·lar":
                selected_category = None
                break
            elif event == "Seleccionar":
                selected_list = values["-SELECTED_CATEGORY-"]
                if selected_list:
                    selected_category = selected_list[0]
                    break

        window.close()
        return selected_category

    def demanar_directori(self):
        """Demana a l'usuari el directori on hi ha els fitxers Norma43."""
        import FreeSimpleGUI as sg
        directori = sg.popup_get_folder("Selecciona el directori amb els fitxers Norma43",
                                        default_path=self._directori_dades,
                                        no_window=False)
        # Si l'usuari cancel·la, retornem el path per defecte
        return directori or self._directori_dades

    # --- Moviments -----------------------------------------------------------

    def _mostrar_resultat(self, resultat):
        """Mostra els moviments a les dues taules (per data i per import) i el resum."""
        parelles = list(zip(resultat.moviments, resultat.saldos_totals))
        per_import = sorted(parelles, key=lambda p: (p[0].import_, p[0].data))
        self.window["-TAULA-"].update(values=files_moviments(*zip(*parelles)) if parelles else [])
        self.window["-TAULA2-"].update(values=files_moviments(*zip(*per_import)) if per_import else [])
        self.window["-Total-"].update(str(resultat.resum.total))
        self.window["-Diari-"].update(str(round(resultat.resum.diari, 2)))
        self.window["-Mensual-"].update(str(round(resultat.resum.mensual, 2)))

    def _filtre_actual(self):
        return construir_filtre(
            self.window["-INPUT_FILTRE-"].get(),
            self.window["-DATA_INICI-"].get(),
            self.window["-DATA_FI-"].get(),
            self.window["-COMBO_CATEGORIA-"].get(),
        )

    def _aplicar_filtres(self):
        """Torna a filtrar els moviments de la sessió amb els valors actuals dels camps."""
        self._mostrar_resultat(self._casos.filtrar_moviments.execute(self._filtre_actual()))

    # --- Categories ----------------------------------------------------------

    def _categories(self):
        return self._casos.llistar_categories.execute()

    def _valors_combo_categories(self):
        return list(self._categories().keys()) + [CATEGORIA_PER_DEFECTE, TOTES]

    def _files_taula_categories(self):
        """Files de la taula de categories, en el mateix ordre que el repositori."""
        return [[nom, ", ".join(paraules)] for nom, paraules in self._categories().items()]

    def _categoria_seleccionada(self, values):
        """Nom de la categoria de la fila seleccionada, o None si no n'hi ha cap."""
        files = values.get("-TABLE_CATEGORIES-") or []
        noms = list(self._categories().keys())
        if files and 0 <= files[0] < len(noms):
            return noms[files[0]]
        return None

    def _actualitzar_categories(self):
        """Actualitza la taula de categories (si està oberta) i el desplegable del filtre."""
        if self._finestra_categories_actual:
            self._finestra_categories_actual["-TABLE_CATEGORIES-"].update(values=self._files_taula_categories())

        combo = self.window["-COMBO_CATEGORIA-"]
        valors = self._valors_combo_categories()
        actual = combo.get()
        combo.update(values=valors, value=actual if actual in valors else TOTES)

    def _afegir_categoria(self):
        nom = self.input_popup("Nom de la nova categoria:", "Nova Categoria")
        if nom is None:
            return
        text = self.input_popup("Paraules clau separades per comes:", "Paraules Clau")
        if text is None:
            return
        paraules = parsejar_paraules_clau(text)
        try:
            self._casos.afegir_categoria.execute(nom, paraules)
        except CategoriaInvalida as e:
            self.mostrar_popup("Error", str(e))
            return
        self.mostrar_popup("Èxit", f"S'ha afegit la categoria '{nom}' amb {len(paraules)} paraules clau.")
        self._actualitzar_categories()

    def _editar_categoria(self, nom=None):
        categories = self._categories()
        if not categories:
            self.mostrar_popup("Error", "No hi ha categories per editar.")
            return
        nom = nom or self.seleccionar_categoria(list(categories.keys()), "Selecciona la categoria a editar:")
        if not nom:
            return
        text = self.input_popup("Editar paraules clau:", "Editar Paraules Clau",
                                default_text=", ".join(categories.get(nom, [])))
        if text is None:  # Cancel·lat: no tocar les paraules clau
            return
        paraules = parsejar_paraules_clau(text)
        try:
            self._casos.editar_categoria.execute(nom, paraules)
        except CategoriaInvalida as e:
            self.mostrar_popup("Error", str(e))
            return
        self.mostrar_popup("Èxit", f"S'ha editat la categoria '{nom}' amb {len(paraules)} paraules clau.")
        self._actualitzar_categories()

    def _eliminar_categoria(self, nom=None):
        categories = self._categories()
        if not categories:
            self.mostrar_popup("Error", "No hi ha categories per eliminar.")
            return
        nom = nom or self.seleccionar_categoria(list(categories.keys()), "Selecciona la categoria a eliminar:")
        if not nom:
            return
        if not self.confirmar_accio(f"Segur que vol eliminar la categoria '{nom}'?"):
            self.mostrar_popup("Cancel·lat", f"S'ha cancel·lat l'eliminació de la categoria '{nom}'.")
            return
        if self._casos.eliminar_categoria.execute(nom):
            self.mostrar_popup("Èxit", f"S'ha eliminat la categoria '{nom}' correctament.")
            self._actualitzar_categories()
        else:
            self.mostrar_popup("Error", f"No s'ha pogut eliminar la categoria '{nom}'.")

    def _obrir_finestra_categories(self):
        """Mostra una finestra amb la llista de categories i permet gestionar-les."""
        import FreeSimpleGUI as sg

        layout = [
            [sg.Text("Gestió de Categories", font=("Arial", 16))],
            [sg.Table(
                values=self._files_taula_categories(),
                headings=["Categoria", "Paraules clau associades"],
                col_widths=[20, 50],
                auto_size_columns=False,
                justification="left",
                key="-TABLE_CATEGORIES-",
                expand_x=True,
                expand_y=True,
                num_rows=10
            )],
            [sg.Button("Afegir Categoria", key="-BTN_AFEGIR-"),
             sg.Button("Editar Categoria", key="-BTN_EDITAR-"),
             sg.Button("Eliminar Categoria", key="-BTN_ELIMINAR-"),
             sg.Button("Tancar", key="-BTN_TANCAR-")]
        ]

        window = sg.Window("Gestió de Categories", layout, modal=True, finalize=True, resizable=True, size=(800, 400))
        self._finestra_categories_actual = window

        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED or event == "-BTN_TANCAR-":
                break
            elif event == "-BTN_AFEGIR-":
                self._afegir_categoria()
            elif event == "-BTN_EDITAR-":
                # Si hi ha una fila seleccionada s'edita directament; si no, es pregunta quina
                self._editar_categoria(self._categoria_seleccionada(values))
            elif event == "-BTN_ELIMINAR-":
                self._eliminar_categoria(self._categoria_seleccionada(values))

        self._finestra_categories_actual = None
        window.close()

        # Tornar a assignar categories als moviments i mantenir els filtres actius
        self._casos.recategoritzar.execute()
        self._aplicar_filtres()

    # --- Despeses i ingressos fixos ---------------------------------------------

    def _obrir_finestra_recurrents(self, titol, cas_us, descripcio, text_total, seccio_config):
        """Mostra les despeses o els ingressos fixos dels moviments del filtre actual."""
        import FreeSimpleGUI as sg

        resultat = cas_us.execute(self._filtre_actual())
        layout = [
            [sg.Text(f"{descripcio} (dels moviments del filtre actual).")],
            [sg.Table(
                values=files_recurrents(resultat.recurrents),
                headings=["Concepte", "Banc", "Categoria", "Periodicitat", "Import (€)", "€/mes",
                          "Càrrecs", "Primer", "Últim", "Estat"],
                auto_size_columns=True,
                justification="left",
                key="-TAULA_RECURRENTS-",
                expand_x=True,
                expand_y=True,
                num_rows=15,
            )],
            [sg.Text(text_total), sg.Text(f"{resultat.import_mensual:.2f} €"),
             sg.Push(), sg.Button("Tancar", key="-BTN_TANCAR-")],
            [sg.Text("Els criteris i què s'inclou o s'exclou es configuren a la secció "
                     f"\"{seccio_config}\" de config.json.", font=("Arial", 14))],
        ]

        window = sg.Window(titol, layout, modal=True, finalize=True, resizable=True, size=(1300, 600))
        while True:
            event, _ = window.read()
            if event in (sg.WIN_CLOSED, "-BTN_TANCAR-"):
                break
        window.close()

    def _obrir_finestra_despeses_fixes(self):
        self._obrir_finestra_recurrents(
            "Despeses fixes", self._casos.despeses_fixes,
            "Despeses que es repeteixen amb un import semblant", "Cost mensual de les actives:",
            "despeses_fixes")

    def _obrir_finestra_ingressos_fixos(self):
        self._obrir_finestra_recurrents(
            "Ingressos fixos", self._casos.ingressos_fixos,
            "Ingressos que es repeteixen amb un import semblant", "Ingrés mensual dels actius:",
            "ingressos_fixos")

    # --- Despeses variables ------------------------------------------------------

    def _obrir_finestra_despeses_variables(self):
        """Mostra la despesa del dia a dia dels moviments del filtre actual, per categories."""
        import FreeSimpleGUI as sg

        despeses = self._casos.despeses_variables.execute(self._filtre_actual())
        layout = [
            [sg.Text("Despesa del dia a dia (dels moviments del filtre actual): sense les despeses fixes, "
                     "els traspassos ni les categories excloses.")],
            [sg.Table(
                values=files_despeses_categoria(despeses),
                headings=["Categoria", "Total (€)", "€/mes", "Moviments", "% del total"],
                auto_size_columns=True,
                justification="left",
                key="-TAULA_CATEGORIES-",
                expand_x=True,
                expand_y=True,
                num_rows=12,
            )],
            [sg.Text(text_resum_despeses_variables(despeses))],
            [sg.Text("Despeses puntuals grosses (no compten al total de dalt):")],
            [sg.Table(
                values=files_despeses_puntuals(despeses),
                headings=["Data", "Concepte", "Banc", "Categoria", "Import (€)"],
                auto_size_columns=True,
                justification="left",
                key="-TAULA_PUNTUALS-",
                expand_x=True,
                expand_y=True,
                num_rows=6,
            )],
            [sg.Text("El llindar de les puntuals i les categories excloses es configuren a la secció "
                     "\"despeses_variables\" de config.json.", font=("Arial", 14)),
             sg.Push(), sg.Button("Tancar", key="-BTN_TANCAR-")],
        ]

        window = sg.Window("Despeses variables", layout, modal=True, finalize=True, resizable=True, size=(1100, 700))
        while True:
            event, _ = window.read()
            if event in (sg.WIN_CLOSED, "-BTN_TANCAR-"):
                break
        window.close()

    # --- Previsió ----------------------------------------------------------------

    def _mostrar_previsio(self):
        """Finestra de la previsió: resum, supòsits i gràfica. No depèn del filtre."""
        import FreeSimpleGUI as sg

        resultat = self._casos.preveure_saldo.execute()
        if not resultat.previsio.data_inici:
            self.mostrar_popup("Previsió", "No hi ha moviments per fer la previsió.")
            return

        layout = [
            [sg.Text(text_resum_previsio(resultat), key="-RESUM_PREVISIO-")],
            [sg.Text("Supòsits (moviments que encara no existeixen):")],
            [sg.Table(
                values=files_suposits(self._casos.llistar_suposits.execute()),
                headings=["Concepte", "Import (€)", "Periodicitat", "Inici", "Fi"],
                col_widths=[25, 12, 12, 12, 12],
                auto_size_columns=False,
                justification="left",
                key="-TAULA_SUPOSITS-",
                expand_x=True,
                expand_y=True,
                num_rows=6,
            )],
            [sg.Button("Afegir supòsit", key="-BTN_AFEGIR-"),
             sg.Button("Eliminar supòsit", key="-BTN_ELIMINAR-")],
            [sg.Text("Ingressos i despeses fixos que s'acaben:")],
            [sg.Table(
                values=files_fixos_acabats(self._casos.llistar_fixos_acabats.execute()),
                headings=["Concepte", "Banc", "Darrer dia"],
                col_widths=[40, 15, 12],
                auto_size_columns=False,
                justification="left",
                key="-TAULA_FIXOS_ACABATS-",
                expand_x=True,
                expand_y=True,
                num_rows=4,
            )],
            [sg.Button("Acabar un fix", key="-BTN_ACABAR_FIX-"),
             sg.Button("Eliminar fix acabat", key="-BTN_ELIMINAR_FIX-")],
            [sg.Button("Veure gràfica", key="-BTN_GRAFICA-"), sg.Push(), sg.Button("Tancar", key="-BTN_TANCAR-")],
        ]
        window = sg.Window("Previsió", layout, modal=True, finalize=True, resizable=True, size=(1300, 800))

        def refrescar():
            nonlocal resultat
            resultat = self._casos.preveure_saldo.execute()
            window["-RESUM_PREVISIO-"].update(text_resum_previsio(resultat))
            window["-TAULA_SUPOSITS-"].update(values=files_suposits(self._casos.llistar_suposits.execute()))
            window["-TAULA_FIXOS_ACABATS-"].update(
                values=files_fixos_acabats(self._casos.llistar_fixos_acabats.execute()))

        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "-BTN_TANCAR-"):
                break
            if event == "-BTN_GRAFICA-":
                self._ui_grafica.mostrar_grafica(resultat.grafica)
            elif event == "-BTN_AFEGIR-":
                if self._formulari_suposit():
                    refrescar()
            elif event == "-BTN_ELIMINAR-":
                files = values.get("-TAULA_SUPOSITS-") or []
                if not files:
                    self.mostrar_popup("Eliminar supòsit", "Selecciona primer el supòsit a la taula.")
                elif self.confirmar_accio("Segur que vols eliminar aquest supòsit?"):
                    self._casos.eliminar_suposit.execute(files[0])
                    refrescar()
            elif event == "-BTN_ACABAR_FIX-":
                if self._formulari_fix_acabat(resultat.previsio):
                    refrescar()
            elif event == "-BTN_ELIMINAR_FIX-":
                files = values.get("-TAULA_FIXOS_ACABATS-") or []
                if not files:
                    self.mostrar_popup("Eliminar fix acabat", "Selecciona primer la fila a la taula.")
                elif self.confirmar_accio("Segur que vols que aquest fix torni a comptar sencer?"):
                    self._casos.eliminar_fix_acabat.execute(files[0])
                    refrescar()
        window.close()

    def _formulari_fix_acabat(self, previsio):
        """Demana quin fix s'acaba i quan, i ho desa. Retorna True si s'ha afegit."""
        import FreeSimpleGUI as sg

        opcions = opcions_fixos(previsio)
        if not opcions:
            self.mostrar_popup("Acabar un fix", "No hi ha ingressos ni despeses fixos actius.")
            return False
        layout = [
            [sg.Text("Quin ingrés o despesa fix s'acaba?")],
            [sg.Combo(list(opcions), key="-FIX-", readonly=True, size=(70, 1))],
            [sg.Text("Darrer dia que es cobra:"), sg.Input(key="-FI-", size=(12, 1)),
             sg.CalendarButton("📅", target="-FI-", format="%Y-%m-%d")],
            [sg.Button("Desar", key="-DESAR-"), sg.Button("Cancel·lar", key="-CANCELAR-")],
        ]
        window = sg.Window("Acabar un fix", layout, modal=True, finalize=True)
        afegit = False
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "-CANCELAR-"):
                break
            if event == "-DESAR-":
                banc, concepte = opcions.get(values["-FIX-"], ("", ""))
                data_fi = llegir_data(values["-FI-"])
                try:
                    if data_fi is None and (values["-FI-"] or "").strip():
                        raise SupositInvalid("La data ha de ser AAAA-MM-DD.")
                    self._casos.acabar_fix.execute(FixAcabat(banc, concepte, data_fi))
                except SupositInvalid as e:
                    self.mostrar_popup("Error", str(e))
                    continue
                afegit = True
                break
        window.close()
        return afegit

    def _formulari_suposit(self):
        """Demana un supòsit nou i el desa. Retorna True si se n'ha afegit un."""
        return self._formulari_periodic("Nou supòsit", "negatiu si és una despesa", llegir_suposit,
                                        self._casos.afegir_suposit)

    def _formulari_periodic(self, titol, ajuda_import, llegir, cas_us):
        """Formulari de concepte, import, periodicitat i dates; desa amb cas_us. True si s'ha afegit."""
        import FreeSimpleGUI as sg

        layout = [
            [sg.Text("Concepte:", size=(12, 1)), sg.Input(key="-CONCEPTE-", size=(30, 1))],
            [sg.Text("Import (€):", size=(12, 1)), sg.Input(key="-IMPORT-", size=(12, 1)),
             sg.Text(ajuda_import, font=("Arial", 14))],
            [sg.Text("Periodicitat:", size=(12, 1)),
             sg.Combo(list(PERIODICITATS), default_value="mensual", key="-PERIODICITAT-", readonly=True)],
            [sg.Text("Inici:", size=(12, 1)), sg.Input(key="-INICI-", size=(12, 1)),
             sg.CalendarButton("📅", target="-INICI-", format="%Y-%m-%d")],
            [sg.Text("Fi (opcional):", size=(12, 1)), sg.Input(key="-FI-", size=(12, 1)),
             sg.CalendarButton("📅", target="-FI-", format="%Y-%m-%d")],
            [sg.Button("Desar", key="-DESAR-"), sg.Button("Cancel·lar", key="-CANCELAR-")],
        ]
        window = sg.Window(titol, layout, modal=True, finalize=True)
        afegit = False
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "-CANCELAR-"):
                break
            if event == "-DESAR-":
                try:
                    cas_us.execute(llegir(values["-CONCEPTE-"], values["-IMPORT-"], values["-PERIODICITAT-"],
                                          values["-INICI-"], values["-FI-"]))
                except SupositInvalid as e:
                    self.mostrar_popup("Error", str(e))
                    continue
                afegit = True
                break
        window.close()
        return afegit

    # --- Pagaments en efectiu -----------------------------------------------------

    def _obrir_finestra_pagaments_efectiu(self):
        """Gestiona els pagaments fixos en efectiu; si canvien, es tornen a carregar els moviments."""
        import FreeSimpleGUI as sg

        def files():
            return files_suposits(self._casos.llistar_pagaments_efectiu.execute())

        layout = [
            [sg.Text("Pagaments fixos que es fan en efectiu, amb diners de les retirades del caixer.\n"
                     "Surten al compte EFECTIU amb la seva categoria, i la categoria de les retirades es redueix\n"
                     "en la mateixa quantitat (\"RETIRADA EFECTIVO ASSIGNADA\"). El saldo total no canvia.",
                     font=("Arial", 14))],
            [sg.Table(
                values=files(),
                headings=["Concepte", "Import (€)", "Periodicitat", "Inici", "Fi"],
                col_widths=[25, 12, 12, 12, 12],
                auto_size_columns=False,
                justification="left",
                key="-TAULA_PAGAMENTS-",
                expand_x=True,
                expand_y=True,
                num_rows=8,
            )],
            [sg.Button("Afegir pagament", key="-BTN_AFEGIR-"),
             sg.Button("Eliminar pagament", key="-BTN_ELIMINAR-"),
             sg.Push(), sg.Button("Tancar", key="-BTN_TANCAR-")],
        ]
        window = sg.Window("Pagaments en efectiu", layout, modal=True, finalize=True, resizable=True, size=(1100, 500))
        canviat = False
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, "-BTN_TANCAR-"):
                break
            if event == "-BTN_AFEGIR-":
                if self._formulari_periodic("Nou pagament en efectiu", "el que es paga, en positiu",
                                            llegir_pagament_efectiu, self._casos.afegir_pagament_efectiu):
                    canviat = True
                    window["-TAULA_PAGAMENTS-"].update(values=files())
            elif event == "-BTN_ELIMINAR-":
                seleccio = values.get("-TAULA_PAGAMENTS-") or []
                if not seleccio:
                    self.mostrar_popup("Eliminar pagament", "Selecciona primer el pagament a la taula.")
                elif self.confirmar_accio("Segur que vols eliminar aquest pagament en efectiu?"):
                    self._casos.eliminar_pagament_efectiu.execute(seleccio[0])
                    canviat = True
                    window["-TAULA_PAGAMENTS-"].update(values=files())
        window.close()

        if canviat and self._directori_carregat is not None:
            self._casos.carregar_moviments.execute(self._directori_carregat)
            self._aplicar_filtres()

    # --- Bucle principal -----------------------------------------------------

    def _carregar(self):
        """Demana el directori, carrega els moviments i els mostra."""
        directori = self.demanar_directori()
        self._directori_carregat = directori
        self._mostrar_resultat(self._casos.carregar_moviments.execute(directori))

    def run(self):
        """Carrega els moviments i executa el bucle principal de la finestra."""
        import FreeSimpleGUI as sg
        self._carregar()

        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED:
                break

            # Les gràfiques mostren els mateixos moviments que la taula: els del filtre actual
            if event == "-BTN_BALANCE-":
                self._ui_grafica.mostrar_grafica(self._casos.grafica_balance.execute(self._filtre_actual()))
            elif event == "-BTN_IMPORTS-":
                self._ui_grafica.mostrar_grafica(self._casos.grafica_imports.execute(self._filtre_actual()))
            elif event == "-BTN_CATEGORIES-":
                self._ui_grafica.mostrar_grafica_categories(self._casos.grafica_categories.execute(self._filtre_actual()))
            elif event == "-BTN_GESTIONAR_CATEGORIES-":
                self._obrir_finestra_categories()
            elif event == "-BTN_DESPESES_FIXES-":
                self._obrir_finestra_despeses_fixes()
            elif event == "-BTN_INGRESSOS_FIXOS-":
                self._obrir_finestra_ingressos_fixos()
            elif event == "-BTN_DESPESES_VARIABLES-":
                self._obrir_finestra_despeses_variables()
            elif event == "-BTN_PREVISIO-":
                self._mostrar_previsio()
            elif event == "-BTN_PAGAMENTS_EFECTIU-":
                self._obrir_finestra_pagaments_efectiu()
            elif event in ["-INPUT_FILTRE-", "-DATA_INICI-", "-DATA_FI-"]:
                # Mentre s'escriu una data incompleta no es refiltra
                if _data_valida_o_buida(values.get("-DATA_INICI-")) and _data_valida_o_buida(values.get("-DATA_FI-")):
                    self._aplicar_filtres()
            elif event == "-COMBO_CATEGORIA-":
                self._aplicar_filtres()

        self.window.close()
