"""Conexao com o MySQL. Os repositorios recebem o cursor criado aqui."""

from contextlib import contextmanager

import pymysql
from flask import current_app


def conectar():
    config = current_app.config
    return pymysql.connect(
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


@contextmanager
def transacao():
    """Entrega um cursor. Confirma tudo no final ou desfaz tudo se ocorrer erro.

    Exemplo: alterar um dispositivo e gravar o historico usam a mesma
    transacao, entao as duas operacoes acontecem juntas ou nenhuma acontece.
    """
    conexao = conectar()
    try:
        with conexao.cursor() as cursor:
            yield cursor
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()
