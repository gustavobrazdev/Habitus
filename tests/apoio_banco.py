"""Banco falso usado pelos testes: guarda os SQL executados e devolve respostas prontas."""

from contextlib import contextmanager
from unittest.mock import patch

import pymysql


class CursorFalso:
    def __init__(self, um=None, todos=None, erro_no_insert=False):
        self.respostas_um = list(um or [])
        self.respostas_todos = list(todos or [])
        self.erro_no_insert = erro_no_insert
        self.comandos = []
        self.lastrowid = 0
        self.rowcount = 1

    def execute(self, sql, valores=None):
        self.comandos.append((" ".join(sql.split()), valores))
        if self.erro_no_insert and sql.lstrip().startswith("INSERT"):
            raise pymysql.err.IntegrityError(1062, "Duplicate entry")
        self.lastrowid += 1

    def fetchone(self):
        return self.respostas_um.pop(0) if self.respostas_um else None

    def fetchall(self):
        return self.respostas_todos.pop(0) if self.respostas_todos else []

    def sql(self, inicio):
        """Comandos que comecam com o texto informado, ex.: 'INSERT INTO rotinas'."""
        return [comando for comando in self.comandos if comando[0].startswith(inicio)]


def transacao_com(cursor):
    """Substituto de app.database.transacao que entrega sempre o cursor falso."""
    @contextmanager
    def transacao_falsa():
        yield cursor
    return transacao_falsa


def usar_banco_falso(monkeypatch, *modulos, **respostas):
    """Troca a transacao dos modulos informados e devolve o cursor falso."""
    cursor = CursorFalso(**respostas)
    for modulo in modulos:
        monkeypatch.setattr(modulo, "transacao", transacao_com(cursor))
    return cursor


def entrar_como(app, perfil, **sessao_extra):
    """Cliente logado na casa 7 como usuario 9 com o perfil escolhido."""
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 9
        sessao["casa_id"] = 7
        sessao["csrf_token"] = "token-teste"
        sessao.update(sessao_extra)
    acesso = {"id_usuario": 9, "nome": "Teste", "perfil": perfil, "id_casa": 7, "nome_casa": "Casa"}
    return cliente, patch("app.carregar_acesso", return_value=acesso)
