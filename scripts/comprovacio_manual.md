# Comprovació manual de la interfície

Per fer després de cada fase del refactor que toqui la interfície (`python3 main.py`).
Abans, `python3 scripts/comprovar_dades.py` ha de dir OK.

## Càrrega
- [ ] Proposa `~/.comptes2` com a directori i, en acceptar, es mostren els moviments a les dues taules.
- [ ] Total, Diari i Mensual tenen valors.
- [ ] Les taules tenen "Balanç del banc" i "Balanç total"; al darrer moviment, el total és la suma de tots els comptes (també amb un filtre posat).

## Filtres
- [ ] Escriure un text filtra les taules i actualitza Total/Diari/Mensual.
- [ ] Data inici i data fi (amb el calendari) filtren correctament.
- [ ] El desplegable de categoria filtra; "Totes" mostra tot.

## Gràfiques
- [ ] Gràfiques › "Balanç" obre la gràfica amb una línia per banc i el Total.
- [ ] Gràfiques › "Imports" obre la gràfica d'imports acumulats.
- [ ] Gràfiques › "Categories" obre la gràfica de despeses per categoria.
- [ ] Amb un filtre actiu, les gràfiques només mostren els moviments filtrats.
- [ ] Les gràfiques de balanç, d'imports i de previsió tenen una línia vertical el dia 1 de cada mes.

## Categories
- [ ] "Gestionar categories" obre la finestra amb la taula.
- [ ] Afegir una categoria: apareix a la taula i al desplegable del filtre.
- [ ] Seleccionar una fila i Editar: no torna a preguntar quina, i proposa les paraules actuals.
- [ ] Seleccionar una fila i Eliminar: demana confirmació i desapareix de la taula i del desplegable.
- [ ] Editar/Eliminar sense fila seleccionada: pregunta quina categoria.
- [ ] En tancar, els moviments es recategoritzen i el filtre que hi havia es manté.
- [ ] Els traspassos entre comptes (una transferència que surt d'un compte i entra a un altre amb el mateix import) surten amb categoria "traspas", també després de gestionar categories.
- [ ] Deixar les categories com estaven (o restaurar `~/.comptes2/categories.json`).

## Despeses i ingressos fixos
- [ ] "Despeses fixes" obre una finestra amb la taula: primer les actives, de més a menys €/mes.
- [ ] Al peu hi ha el cost mensual de les actives.
- [ ] "Ingressos fixos" obre la mateixa finestra amb els ingressos (nòmines, etc.) i l'ingrés mensual.
- [ ] Amb un filtre actiu (p. ex. una categoria o una data fi), només hi surten les d'aquells moviments.
- [ ] "Tancar" i la creu tanquen la finestra i es torna a la principal.

## Extractes de targeta
- [ ] Amb un `<banc>_targeta_*.xls` al directori, la taula té moviments del banc `<banc>_targeta` amb el nom del comerç i categoria.
- [ ] Per cada dia amb compres hi ha un "CREDITO TARJETA ASSIGNADA" positiu, a la categoria dels càrrecs de la targeta.
- [ ] El saldo total del darrer moviment és el mateix que sense l'extracte.
- [ ] No hi ha cap "REINTEGRO EN CAJERO" (les retirades ja surten al compte).

## Despeses variables
- [ ] Els botons estan en tres files (Gràfiques, Anàlisi, Configuració) i es veuen tots amb la mida inicial de la finestra.
- [ ] "Despeses variables" obre la taula per categories (de més a menys), amb €/mes i % del total; no hi surten "traspas", "estalvi" ni "amortitzacio".
- [ ] El resum diu el total, els mesos del període, els €/mes i el total de les puntuals.
- [ ] A sota, les despeses de més de 1.000 € (sense les amortitzacions), de la més grossa a la més petita.
- [ ] Canviant les dates del filtre canvien els mesos i la mitjana; filtrant un sol mes, la mútua i els altres fixos continuen fora.

## Previsió
- [ ] El "Saldo actual" del resum inclou el SIALP (coincideix amb la columna "Balanç total" del darrer moviment), i la línia de la resta diu "sense amortitzacio, obres".
- [ ] "Previsió" obre una finestra amb el resum (saldo actual, ingressos i despeses fixos, resta de moviments i saldo previst a 3, 6 i 12 mesos) i la taula de supòsits.
- [ ] "Veure gràfica" obre la gràfica amb el saldo total real (línia contínua) i la previsió (discontínua) que continua on acaba el real, sense el SIALP.
- [ ] Amb un filtre actiu, la previsió és la mateixa (no depèn del filtre).
- [ ] "Afegir supòsit": amb un import o una data dolents surt un error i el formulari es queda obert; amb dades bones, el supòsit surt a la taula, al "Inclou els supòsits" del resum, i el saldo previst canvia.
- [ ] "Veure gràfica": només hi ha el saldo real i una línia "Previsió" (que ja inclou els supòsits) amb la franja "Rang probable".
- [ ] El supòsit es manté en tancar i tornar a obrir l'aplicació (és a `config.json`, secció `previsio`).
- [ ] "Eliminar supòsit" sense fila seleccionada avisa; amb fila, demana confirmació i desapareix.
- [ ] El resum dona per a cada saldo previst el rang probable ("entre X i Y"), i la gràfica té la franja grisa "Rang probable" que s'eixampla amb el temps.
- [ ] "Acabar un fix": el desplegable mostra els ingressos i despeses fixos actius; sense triar-ne cap o amb una data dolenta surt un error; amb dades bones surt a la taula i al "Inclou els supòsits" del resum.
- [ ] "Eliminar fix acabat" sense fila seleccionada avisa; amb fila, demana confirmació i desapareix.

## Pagaments en efectiu
- [ ] "Pagaments en efectiu" obre la finestra amb la taula i l'explicació.
- [ ] "Afegir pagament": amb un import negatiu o una data dolenta surt un error; amb dades bones surt a la taula.
- [ ] En tancar, la taula principal té els moviments del compte EFECTIU (despesa i "RETIRADA EFECTIVO ASSIGNADA") i el Total no canvia.
- [ ] A la gràfica de categories, la del pagament creix i "efectiu" es redueix en la mateixa quantitat.
- [ ] Si es repeteix prou, el pagament surt a "Despeses fixes" i no hi ha cap "RETIRADA EFECTIVO ASSIGNADA" a "Ingressos fixos".
- [ ] "Eliminar pagament" sense fila avisa; amb fila, demana confirmació i, en tancar, els moviments desapareixen.
