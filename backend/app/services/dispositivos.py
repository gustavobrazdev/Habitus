"""Cadastro, controle e remocao de dispositivos."""

from app.database import transacao
from app.models.dispositivo import CLASSES, configuracao_inicial, criar_dispositivo
from app.repositories import comodos as repo_comodos
from app.repositories import dispositivos as repo_dispositivos
from app.repositories import historico as repo_historico
from app.repositories import rotinas as repo_rotinas
from app.validators.dispositivos import validar_dispositivo


def dados_da_pagina(id_casa):
    with transacao() as cursor:
        return {
            "dispositivos": repo_dispositivos.listar_ativos_da_casa(cursor, id_casa),
            "comodos": repo_comodos.listar(cursor, id_casa),
        }


def cadastrar_dispositivo(id_casa, nome, tipo, id_comodo):
    dados = validar_dispositivo(nome, tipo, id_comodo)
    with transacao() as cursor:
        if not repo_comodos.buscar(cursor, id_casa, dados["id_comodo"]):
            raise ValueError("Escolha um comodo da sua casa.")
        return repo_dispositivos.inserir(cursor, dados["id_comodo"], dados["nome"],
                                         dados["tipo"], configuracao_inicial(dados["tipo"]))


def salvar_alteracao(cursor, id_dispositivo, id_usuario, acao, alteracao):
    """Atualiza o controle e grava o historico usando a mesma transacao."""
    campo, anterior, novo = alteracao
    repo_dispositivos.atualizar_campo(cursor, id_dispositivo, campo, novo)
    repo_historico.registrar(cursor, id_dispositivo, id_usuario, acao, anterior, novo)
    return {"campo": campo, "antes": anterior, "depois": novo}


def alterar_dispositivo(id_dispositivo, id_casa, id_usuario, acao, valor=None):
    """So permite controlar dispositivos da casa que esta aberta."""
    with transacao() as cursor:
        dados = repo_dispositivos.buscar_ativo(cursor, id_dispositivo, id_casa, bloquear=True)
        if dados is None:
            raise ValueError("Dispositivo nao encontrado nessa casa.")
        # Polimorfismo: cada classe executa e valida a acao do seu jeito.
        alteracao = criar_dispositivo(dados).executar(acao, valor)
        return salvar_alteracao(cursor, id_dispositivo, id_usuario, acao, alteracao)


def remover_dispositivo(id_casa, id_dispositivo):
    """Tira da lista e pausa as rotinas. O historico continua salvo."""
    with transacao() as cursor:
        if not repo_dispositivos.desativar(cursor, id_dispositivo, id_casa):
            raise ValueError("Dispositivo nao encontrado.")
        repo_rotinas.pausar_do_dispositivo(cursor, id_dispositivo)


def ajustes_por_tipo():
    """Controle extra de cada tipo (ou None), usado para montar os cards."""
    return {tipo: classe.ajuste for tipo, classe in CLASSES.items()}
