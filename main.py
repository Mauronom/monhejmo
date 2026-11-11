from infra import (RepositoriMovimentsNorma43, RepositoriCategoria, JsonConfigMovimentsFicticisRepo,
                   JsonConfigRecurrentsRepo, JsonConfigPrevisioRepo, JsonRepositoriSuposits,
                   JsonRepositoriFixosAcabats, JsonRepositoriPagamentsEfectiu,
                   JsonConfigDespesesVariablesRepo,
                   UIBokeh, UIFreeSimpleGUI, resoldre_directori_dades)
from app import CasosUs, MovimentsSessio

if __name__ == "__main__":
    directori_dades = resoldre_directori_dades()
    casos_us = CasosUs.construir(
        font=RepositoriMovimentsNorma43(),
        config_ficticis=JsonConfigMovimentsFicticisRepo(directori_dades / "config.json"),
        repositori_categories=RepositoriCategoria(directori=directori_dades),
        sessio=MovimentsSessio(),
        config_despeses_fixes=JsonConfigRecurrentsRepo(directori_dades / "config.json", "despeses_fixes"),
        config_ingressos_fixos=JsonConfigRecurrentsRepo(directori_dades / "config.json", "ingressos_fixos"),
        config_previsio=JsonConfigPrevisioRepo(directori_dades / "config.json"),
        repositori_suposits=JsonRepositoriSuposits(directori_dades / "config.json"),
        repositori_fixos_acabats=JsonRepositoriFixosAcabats(directori_dades / "config.json"),
        repositori_pagaments_efectiu=JsonRepositoriPagamentsEfectiu(directori_dades / "config.json"),
        config_despeses_variables=JsonConfigDespesesVariablesRepo(directori_dades / "config.json"),
    )
    UIFreeSimpleGUI(casos_us, UIBokeh(), directori_dades).run()
