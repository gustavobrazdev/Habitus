"""Regras dos comodos e da transferencia de dispositivos entre eles.

Todas as funcoes recebem o id da casa aberta, assim um administrador nunca
altera comodos ou dispositivos de outra residencia.
"""

import pymysql

from app.database import transacao
from app.models.comodo import COMODOS_SUGERIDOS, Comodo
from app.models.dispositivo import configuracao_inicial
from app.repositories import comodos as repo_comodos
from app.repositories import dispositivos as repo_dispositivos
from app.repositories import historico as repo_historico

MENSAGEM_DUPLICADO = "Ja existe um comodo com esse nome nesta casa."

# Dispositivos de exemplo criados junto com os comodos sugeridos.
EXEMPLOS = {"Sala": ("Luz da sala", "luz"), "Quarto": ("Ar do quarto", "ar_condicionado")}


def listar_comodos(id_casa):
    with transacao() as cursor:
        return repo_comodos.listar_com_dispositivos(cursor, id_casa)


def nome_em_uso(cursor, id_casa, comodo, ignorar_id=None):
    """Compara no Python para nao depender da collation do MySQL."""
    for existente in repo_comodos.listar(cursor, id_casa):
        if existente["id_comodo"] != ignorar_id and comodo.tem_mesmo_nome(existente["nome"]):
            return True
    return False


def criar_comodos_iniciais(cursor, id_casa, opcao):
    """'sugeridos' cria Sala, Quarto e Cozinha; 'vazio' nao cria nada."""
    if opcao == "vazio":
        return []
    for nome in COMODOS_SUGERIDOS:
        id_comodo = repo_comodos.inserir(cursor, id_casa, nome)
        if nome in EXEMPLOS:
            nome_dispositivo, tipo = EXEMPLOS[nome]
            repo_dispositivos.inserir(cursor, id_comodo, nome_dispositivo, tipo,
                                      configuracao_inicial(tipo))
    return list(COMODOS_SUGERIDOS)


def criar_comodo(id_casa, nome):
    comodo = Comodo(nome)
    try:
        with transacao() as cursor:
            if nome_em_uso(cursor, id_casa, comodo):
                raise ValueError(MENSAGEM_DUPLICADO)
            comodo.id_comodo = repo_comodos.inserir(cursor, id_casa, comodo.nome)
    except pymysql.err.IntegrityError:
        # O indice UNIQUE (id_casa, nome) barra dois cadastros ao mesmo tempo.
        raise ValueError(MENSAGEM_DUPLICADO)
    return comodo


def renomear_comodo(id_casa, id_comodo, novo_nome):
    comodo = Comodo(novo_nome, id_comodo)
    try:
        with transacao() as cursor:
            if not repo_comodos.buscar(cursor, id_casa, id_comodo, bloquear=True):
                raise ValueError("Comodo nao encontrado nesta casa.")
            if nome_em_uso(cursor, id_casa, comodo, ignorar_id=id_comodo):
                raise ValueError(MENSAGEM_DUPLICADO)
            repo_comodos.renomear(cursor, id_casa, id_comodo, comodo.nome)
    except pymysql.err.IntegrityError:
        raise ValueError(MENSAGEM_DUPLICADO)
    return comodo


def excluir_comodo(id_casa, id_comodo):
    """So apaga comodos vazios. Dispositivos nunca sao removidos junto."""
    with transacao() as cursor:
        comodo = repo_comodos.buscar(cursor, id_casa, id_comodo, bloquear=True)
        if not comodo:
            raise ValueError("Comodo nao encontrado nesta casa.")

        # Conta tambem os dispositivos removidos da lista: eles guardam o historico.
        contagem = repo_comodos.contar_dispositivos(cursor, id_comodo)
        if int(contagem["ativos"]):
            raise ValueError(
                f"O comodo {comodo['nome']} possui {int(contagem['ativos'])} dispositivo(s). "
                "Transfira-os para outro ambiente antes de excluir."
            )
        if int(contagem["total"]):
            raise ValueError(
                f"O comodo {comodo['nome']} guarda o historico de dispositivos removidos "
                "e por isso nao pode ser excluido."
            )
        repo_comodos.excluir(cursor, id_casa, id_comodo)
    return comodo["nome"]


def transferir_dispositivo(id_casa, id_dispositivo, id_comodo_destino, id_usuario):
    """Muda somente o comodo. Configuracoes, rotinas e historico continuam
    ligados ao mesmo id_dispositivo, por isso nada e perdido."""
    with transacao() as cursor:
        dispositivo = repo_dispositivos.buscar_ativo(cursor, id_dispositivo, id_casa, bloquear=True)
        if not dispositivo:
            raise ValueError("Dispositivo nao encontrado nesta casa.")
        destino = repo_comodos.buscar(cursor, id_casa, id_comodo_destino, bloquear=True)
        if not destino:
            raise ValueError("Escolha um comodo desta casa.")
        if destino["id_comodo"] == dispositivo["id_comodo"]:
            raise ValueError("O dispositivo ja esta nesse comodo.")

        repo_dispositivos.mudar_comodo(cursor, id_dispositivo, destino["id_comodo"])
        repo_historico.registrar(cursor, id_dispositivo, id_usuario, "transferir_comodo",
                                 dispositivo["nome_comodo"], destino["nome"])
    return dispositivo["nome"], destino["nome"]
