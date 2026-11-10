from dataclasses import dataclass
from .carregar_moviments import CarregarMoviments
from .filtrar_moviments import FiltrarMoviments
from .recategoritzar import Recategoritzar
from .grafica_balance import GraficaBalance
from .grafica_imports import GraficaImports
from .grafica_categories import GraficaCategories
from .llistar_categories import LlistarCategories
from .afegir_categoria import AfegirCategoria
from .editar_categoria import EditarCategoria
from .eliminar_categoria import EliminarCategoria
from .moviments_recurrents import MovimentsRecurrents
from .preveure_saldo import PreveureSaldo
from .suposits import (LlistarSuposits, AfegirSuposit, EliminarSuposit, LlistarFixosAcabats, AcabarFix,
                       EliminarFixAcabat, LlistarPagamentsEfectiu, AfegirPagamentEfectiu,
                       EliminarPagamentEfectiu)


@dataclass(frozen=True)
class CasosUs:
    """Tots els casos d'ús de l'aplicació, ja construïts. És el que necessita una interfície."""
    carregar_moviments: CarregarMoviments
    filtrar_moviments: FiltrarMoviments
    recategoritzar: Recategoritzar
    grafica_balance: GraficaBalance
    grafica_imports: GraficaImports
    grafica_categories: GraficaCategories
    llistar_categories: LlistarCategories
    afegir_categoria: AfegirCategoria
    editar_categoria: EditarCategoria
    eliminar_categoria: EliminarCategoria
    despeses_fixes: MovimentsRecurrents
    ingressos_fixos: MovimentsRecurrents
    preveure_saldo: PreveureSaldo
    llistar_suposits: LlistarSuposits
    afegir_suposit: AfegirSuposit
    eliminar_suposit: EliminarSuposit
    llistar_fixos_acabats: LlistarFixosAcabats
    acabar_fix: AcabarFix
    eliminar_fix_acabat: EliminarFixAcabat
    llistar_pagaments_efectiu: LlistarPagamentsEfectiu
    afegir_pagament_efectiu: AfegirPagamentEfectiu
    eliminar_pagament_efectiu: EliminarPagamentEfectiu

    @classmethod
    def construir(cls, font, config_ficticis, repositori_categories, sessio,
                  config_despeses_fixes, config_ingressos_fixos, config_previsio, repositori_suposits,
                  repositori_fixos_acabats, repositori_pagaments_efectiu):
        return cls(
            carregar_moviments=CarregarMoviments(font, config_ficticis, repositori_categories, sessio,
                                                 repositori_pagaments_efectiu),
            filtrar_moviments=FiltrarMoviments(sessio),
            recategoritzar=Recategoritzar(sessio, repositori_categories),
            grafica_balance=GraficaBalance(sessio),
            grafica_imports=GraficaImports(sessio),
            grafica_categories=GraficaCategories(sessio),
            llistar_categories=LlistarCategories(repositori_categories),
            afegir_categoria=AfegirCategoria(repositori_categories),
            editar_categoria=EditarCategoria(repositori_categories),
            eliminar_categoria=EliminarCategoria(repositori_categories),
            despeses_fixes=MovimentsRecurrents(sessio, config_despeses_fixes),
            ingressos_fixos=MovimentsRecurrents(sessio, config_ingressos_fixos, ingressos=True),
            preveure_saldo=PreveureSaldo(sessio, config_despeses_fixes, config_ingressos_fixos, config_previsio,
                                         repositori_suposits, repositori_fixos_acabats),
            llistar_suposits=LlistarSuposits(repositori_suposits),
            afegir_suposit=AfegirSuposit(repositori_suposits),
            eliminar_suposit=EliminarSuposit(repositori_suposits),
            llistar_fixos_acabats=LlistarFixosAcabats(repositori_fixos_acabats),
            acabar_fix=AcabarFix(repositori_fixos_acabats),
            eliminar_fix_acabat=EliminarFixAcabat(repositori_fixos_acabats),
            llistar_pagaments_efectiu=LlistarPagamentsEfectiu(repositori_pagaments_efectiu),
            afegir_pagament_efectiu=AfegirPagamentEfectiu(repositori_pagaments_efectiu),
            eliminar_pagament_efectiu=EliminarPagamentEfectiu(repositori_pagaments_efectiu),
        )
