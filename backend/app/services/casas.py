"""Dados da casa aberta: painel, troca de casa e historico."""

from collections import defaultdict

from app.database import transacao
from app.repositories import casas as repo_casas
from app.repositories import comodos as repo_comodos
from app.repositories import dispositivos as repo_dispositivos
from app.repositories import historico as repo_historico
from app.repositories import moradores as repo_moradores
from app.repositories import rotinas as repo_rotinas


def casas_do_usuario(id_usuario):
    with transacao() as cursor:
        return repo_casas.listar_do_usuario(cursor, id_usuario)


def pode_abrir_casa(id_usuario, id_casa):
    with transacao() as cursor:
        return repo_moradores.participa(cursor, id_usuario, id_casa)


def resumo_do_painel(id_casa):
    with transacao() as cursor:
        comodos = repo_comodos.listar(cursor, id_casa)
        dispositivos = repo_dispositivos.listar_ativos_da_casa(cursor, id_casa)
        eventos = repo_historico.listar_da_casa(cursor, id_casa, limite=6)
        total_rotinas = repo_rotinas.contar_ativas(cursor, id_casa)

    # Dicionario de listas: agrupa os dispositivos de cada comodo para a tela.
    por_comodo = defaultdict(list)
    for dispositivo in dispositivos:
        por_comodo[dispositivo["id_comodo"]].append(dispositivo)

    return {
        "comodos": comodos,
        "dispositivos": dispositivos,
        "por_comodo": por_comodo,
        "ligados": sum(bool(d["ligado"]) for d in dispositivos),
        "ultimos_eventos": eventos,
        "total_rotinas": total_rotinas,
    }


def historico_da_casa(id_casa):
    with transacao() as cursor:
        return repo_historico.listar_da_casa(cursor, id_casa, limite=100)
