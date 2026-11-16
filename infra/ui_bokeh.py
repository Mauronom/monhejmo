import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from itertools import accumulate
from domain import sumar_per_node


def hores_dels_punts(punts):
    """
    Hora a la qual es dibuixa cada punt, perquè els moviments d'un mateix dia quedin en ordre:
    una hora per posició si n'hi ha 24 o menys aquell dia; si n'hi ha més, es reparteixen dins del dia.
    Retorna una llista paral·lela a punts.
    """
    posicions_per_dia = defaultdict(int)
    for p in punts:
        posicions_per_dia[p.data] = max(posicions_per_dia[p.data], p.ordre + 1)

    def pas(n):
        return timedelta(hours=1) if n <= 24 else timedelta(days=1) / n

    return [datetime.combine(p.data, datetime.min.time()) + p.ordre * pas(posicions_per_dia[p.data]) for p in punts]

def inicis_de_mes_entre(inici, fi):
    """El dia 1 de cada mes, des del mes d'inici fins a fi (inclòs)."""
    dia = inici.replace(day=1)
    resultat = []
    while dia <= fi:
        resultat.append(dia)
        dia = date(dia.year + dia.month // 12, dia.month % 12 + 1, 1)
    return resultat


# Prou baixa perquè hi càpiga sencera en la pantalla d'un portàtil, amb la barra del navegador
ALCADA_GRAFICA = 600


def _ms(dia):
    """Mil·lisegons des de 1970 (com Bokeh representa les dates de l'eix)."""
    return (datetime.combine(dia, datetime.min.time()) - datetime(1970, 1, 1)).total_seconds() * 1000


COLORS_PASTIS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22',
    '#17becf', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d3', '#c7c7c7',
    '#dbdb8d', '#9edae5',
]


def desglossos_categories(imports):
    """
    {node: {fill: import}} per a l'arrel ("") i per a cada node que té subcategories, perquè la
    gràfica de categories pugui desglossar qualsevol porció sense tornar a calcular res.
    """
    resultat = {}

    def afegir(node):
        fills = sumar_per_node(imports, node or None)
        resultat[node] = fills
        for fill in fills:
            if fill != node and set(sumar_per_node(imports, fill)) != {fill}:
                afegir(fill)

    afegir("")
    return resultat


def columnes_pastis(valors):
    """Columnes d'un diagrama circular a partir de {categoria: import} (es fa servir el valor absolut)."""
    quantitats = [abs(v) for v in valors.values()]
    total = sum(quantitats)
    finals = list(accumulate(q / total * 2 * math.pi for q in quantitats)) if total else []
    return {
        "categoria": list(valors),
        "quantitat": quantitats,
        "percentatge": [round(q / total * 100, 2) for q in quantitats] if total else [],
        "angle_start": [0.0] + finals[:-1] if finals else [],
        "angle_end": finals,
        "color": [COLORS_PASTIS[i % len(COLORS_PASTIS)] for i in range(len(quantitats))],
    }


class UIBokeh:
    def mostrar_grafica(self, dades: dict):
        from bokeh.plotting import figure, show
        from bokeh.models import ColumnDataSource, HoverTool, FixedTicker
        

        punts = dades["punts"]
        etiqueta_x = dades["etiqueta_x"]
        etiqueta_y = dades["etiqueta_y"]

        if not punts:
            print("No hi ha dades per mostrar")
            return

        # Agrupar punts per banc
        per_banc = defaultdict(list)
        for p, hora in zip(punts, hores_dels_punts(punts)):
            # Convertim Decimal -> float
            per_banc[p.banc].append((hora, float(p.saldo), p.concepte, float(p.import_)))

        # Crear la figura
        p = figure(
            x_axis_type="datetime",
            sizing_mode="stretch_width",  # ocupa l'amplada del navegador, sigui quina sigui
            height=ALCADA_GRAFICA,
            title=dades.get("titol", "Evolució per banc"),
            tools="pan,wheel_zoom,box_zoom,reset,save"
        )
        p.xaxis.axis_label = etiqueta_x
        p.yaxis.axis_label = etiqueta_y
        # Una línia vertical per mes (cada dia 1), sense canviar les etiquetes de l'eix
        dates = [p_.data for p_ in punts]
        p.xgrid.ticker = FixedTicker(ticks=[_ms(d) for d in inicis_de_mes_entre(min(dates), max(dates))])
        p.xgrid.grid_line_alpha = 0.6

        colors = ["blue", "red", "green", "orange", "purple", "brown"]
        discontinues = dades.get("linies_discontinues", ())
        for i, (banc, punts_banc) in enumerate(per_banc.items()):
            punts_banc.sort(key=lambda p: p[0])
            x = [p[0] for p in punts_banc]
            y = [p[1] for p in punts_banc]
            conceptes = [p[2] for p in punts_banc]
            import_s = [p[3] for p in punts_banc]

            source = ColumnDataSource(data={"x": x, "y": y, "banc": [banc]*len(x), "concepte": conceptes, "import_": import_s})

            p.line("x", "y", source=source, line_width=2, color=colors[i % len(colors)], legend_label=banc,
                   line_dash="dashed" if banc in discontinues else "solid")
            p.circle("x", "y", source=source, size=6, color=colors[i % len(colors)], legend_label=banc)

        for franja in dades.get("franges", []):
            dates = [datetime.combine(d, datetime.min.time()) for d in franja["dates"]]
            p.varea(x=dates, y1=[float(v) for v in franja["baix"]], y2=[float(v) for v in franja["alt"]],
                    fill_color=franja.get("color", "gray"), fill_alpha=0.15, legend_label=franja["nom"])

        hover = HoverTool(
            renderers=[r for r in p.renderers if r.glyph.__class__.__name__ != "VArea"],
            tooltips=[
                ("Data", "@x{%F %H:%M}"),
                ("Balanç", "@y{0.00}"),
                ("Import", "@import_{0.00}"),
                ("Concepte", "@concepte"),
                ("Banc", "@banc"),
            ],
            formatters={
                "@x": "datetime",
                "@y": "numeral",
                "@import_": "numeral"
            },
            mode="vline"
        )
        p.add_tools(hover)

        p.legend.location = "top_left"
        p.legend.click_policy = "hide"

        show(p)
    
    def mostrar_grafica_categories(self, despeses_dict, titol="Distribució de Despeses", width=500, height=500):
        """
        Diagrama circular de les despeses per categoria (despeses_dict: {categoria: import net}), al
        primer nivell de l'arbre. En clicar una porció, al costat surt un altre diagrama amb el seu
        desglòs; clicant-hi una porció que tingui subcategories, es baixa un nivell més. Tot es
        calcula aquí i el clic es resol al navegador, perquè la gràfica és un HTML estàtic.
        """
        from bokeh.plotting import figure, show
        from bokeh.layouts import column, row
        from bokeh.models import Button, ColumnDataSource, CustomJS, HoverTool, TapTool

        desglossos = desglossos_categories(despeses_dict)
        columnes = {node: columnes_pastis(valors) for node, valors in desglossos.items()}

        def pastis(titol_pastis, dades):
            font = ColumnDataSource(data=dades)
            p = figure(height=height, width=width, title=titol_pastis, toolbar_location=None, tools="",
                       x_range=(-1.1, 1.1), y_range=(-1.1, 1.1))
            p.axis.visible = False
            p.grid.visible = False
            p.wedge(x=0, y=0, radius=1, start_angle="angle_start", end_angle="angle_end", color="color",
                    source=font, line_color="white", line_width=2)
            p.add_tools(TapTool(), HoverTool(tooltips=[("Categoria", "@categoria"),
                                                       ("Quantitat", "@quantitat{0.00}€"),
                                                       ("Percentatge", "@percentatge{0.00}%")]))
            return p, font

        principal, font_principal = pastis(f"{titol} (clica una porció per desglossar-la)", columnes[""])
        desglos, font_desglos = pastis("Desglòs", columnes_pastis({}))

        mostrar = """
            function mostrar(categoria) {
                if (dades[categoria]) {
                    desglos.data = dades[categoria];
                    titol.text = "Desglòs de " + categoria;
                } else {
                    desglos.data = buit;
                    titol.text = categoria + " no té subcategories";
                }
                desglos.selected.indices = [];
            }
        """
        args = dict(dades=columnes, buit=columnes_pastis({}), desglos=font_desglos, titol=desglos.title)
        font_principal.selected.js_on_change("indices", CustomJS(args=dict(args, font=font_principal), code=mostrar + """
            const i = cb_obj.indices;
            if (i.length) mostrar(font.data.categoria[i[0]]);
        """))
        font_desglos.selected.js_on_change("indices", CustomJS(args=args, code=mostrar + """
            const i = cb_obj.indices;
            if (!i.length) return;
            const categoria = desglos.data.categoria[i[0]];
            // La part del node mateix (sense subcategoria) té el seu nom: no es pot desglossar més
            if (dades[categoria] && "Desglòs de " + categoria != titol.text) mostrar(categoria);
        """))
        # Treu les seleccions (les porcions no seleccionades queden esvaïdes) i amaga el desglòs
        inici = Button(label="Tornar a l'inici", width=150)
        inici.js_on_click(CustomJS(args=dict(args, font=font_principal), code="""
            font.selected.indices = [];
            desglos.data = buit;
            desglos.selected.indices = [];
            titol.text = "Desglòs";
        """))
        show(column(inici, row(principal, desglos)))
