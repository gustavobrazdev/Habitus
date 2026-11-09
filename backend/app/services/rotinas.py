"""Cadastro de rotinas e execucao automatica nos horarios programados."""

from datetime import datetime, timedelta

import pymysql

from app.database import transacao
from app.models.dispositivo import AJUSTES, CLASSES, criar_dispositivo
from app.models.rotina import Rotina, dias_do_texto, formatar_horario
from app.repositories import dispositivos as repo_dispositivos
from app.repositories import rotinas as repo_rotinas
from app.services.dispositivos import salvar_alteracao
from app.structures.fila_rotinas import FilaRotinas
from app.validators.rotinas import validar_rotina

# Se o executor ficar parado, so recupera rotinas atrasadas ate esse limite.
ATRASO_MAXIMO = timedelta(minutes=10)


# ---------------------------------------------------------------- cadastro

def dados_da_pagina(id_casa):
    with transacao() as cursor:
        linhas = repo_rotinas.listar_da_casa(cursor, id_casa)
        dispositivos = repo_dispositivos.listar_ativos_da_casa(cursor, id_casa)
    for dispositivo in dispositivos:
        # O formulario so mostra as acoes que a classe do dispositivo aceita.
        dispositivo["acoes"] = " ".join(sorted(CLASSES[dispositivo["tipo"]].acoes_permitidas))
    return {"rotinas": [Rotina(linha) for linha in linhas],
            "dispositivos": dispositivos, "ajustes": AJUSTES}


def buscar_rotina(id_casa, id_rotina):
    with transacao() as cursor:
        dados = repo_rotinas.buscar_da_casa(cursor, id_rotina, id_casa)
    return Rotina(dados) if dados else None


def salvar_rotina(id_casa, formulario, id_rotina=None):
    """Cria (id_rotina=None) ou edita uma rotina da casa.

    A classe do dispositivo valida a acao e o valor em um objeto na memoria:
    o aparelho nao muda agora, apenas no horario programado.
    """
    dados = validar_rotina(formulario)
    with transacao() as cursor:
        dispositivo = repo_dispositivos.buscar_ativo(cursor, dados["id_dispositivo"], id_casa)
        if not dispositivo:
            raise ValueError("Dispositivo nao encontrado nesta casa.")
        _, _, valor_validado = criar_dispositivo(dispositivo).executar(dados["acao"], dados["valor"])
        dados["valor"] = valor_validado if dados["acao"].startswith("ajustar_") else None

        if id_rotina is None:
            return repo_rotinas.inserir(cursor, dados)
        if not repo_rotinas.buscar_da_casa(cursor, id_rotina, id_casa, bloquear=True):
            raise ValueError("Rotina nao encontrada nesta casa.")
        repo_rotinas.atualizar(cursor, id_rotina, dados)
        return id_rotina


def alternar_rotina(id_casa, id_rotina):
    with transacao() as cursor:
        if not repo_rotinas.buscar_da_casa(cursor, id_rotina, id_casa, bloquear=True):
            raise ValueError("Rotina nao encontrada nesta casa.")
        repo_rotinas.alternar(cursor, id_rotina)


def remover_rotina(id_casa, id_rotina):
    with transacao() as cursor:
        if not repo_rotinas.buscar_da_casa(cursor, id_rotina, id_casa, bloquear=True):
            raise ValueError("Rotina nao encontrada nesta casa.")
        repo_rotinas.excluir(cursor, id_rotina)


# ---------------------------------------------------------------- execucao

def dia_permitido(dias_semana, data):
    """O conjunto de dias permite verificar rapidamente se a data foi escolhida."""
    return str(data.weekday()) in dias_do_texto(dias_semana)


def rotina_pendente(rotina, agendado):
    """A rotina deve rodar nesse horario agendado e ainda nao rodou?"""
    ultima = rotina["ultima_execucao"]
    return (
        bool(rotina["ativa"])
        and formatar_horario(rotina["horario"]) == agendado.strftime("%H:%M")
        and dia_permitido(rotina["dias_semana"], agendado)
        and (ultima is None or ultima < agendado)
    )


def executar_rotina(id_rotina, agendado, agora):
    """Executa uma rotina em uma transacao. Devolve False se nao precisava mais rodar."""
    with transacao() as cursor:
        # Le de novo com bloqueio: a rotina pode ter sido editada, pausada ou ja
        # executada por outro processo depois que a fila foi montada.
        atual = repo_rotinas.buscar_por_id(cursor, id_rotina, bloquear=True)
        if not atual or not rotina_pendente(atual, agendado):
            return False
        dados = repo_dispositivos.buscar_ativo(cursor, atual["id_dispositivo"], bloquear=True)
        if not dados:
            return False

        alteracao = criar_dispositivo(dados).executar(atual["acao"], atual["valor"])
        salvar_alteracao(cursor, atual["id_dispositivo"], None,
                         f"Rotina: {atual['nome']}", alteracao)
        repo_rotinas.marcar_execucao(cursor, id_rotina, agora)
        return True


def executar_pendentes(agora=None, desde=None):
    """Executa as rotinas com horario entre `desde` e `agora`.

    Devolve (nomes executados, mensagens de falha). Uma falha em uma rotina
    nao impede as proximas da fila de serem executadas.
    """
    agora = agora or datetime.now()
    desde = max(desde or agora - timedelta(minutes=1), agora - ATRASO_MAXIMO)

    with transacao() as cursor:
        rotinas = repo_rotinas.listar_ativas(cursor)

    agenda = FilaRotinas(rotinas, desde)                         # heapq: ordena pelo horario
    comandos = agenda.comandos_ate(agora, rotina_pendente)       # deque: fila FIFO
    executadas, falhas = [], []

    while comandos:
        rotina, agendado = comandos.popleft()
        try:
            if executar_rotina(rotina["id_rotina"], agendado, agora):
                executadas.append(rotina["nome"])
        except (ValueError, pymysql.MySQLError) as erro:
            falhas.append(f"{rotina['nome']}: {erro}")

    return executadas, falhas
