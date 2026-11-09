"""Moradores: cadastro (com conta nova ou existente), permissao e remocao."""

import secrets

import pymysql
from werkzeug.security import generate_password_hash

from app.database import transacao
from app.repositories import moradores as repo_moradores
from app.repositories import usuarios as repo_usuarios
from app.validators.usuarios import validar_email, validar_nome, validar_perfil

# Sem letras e numeros parecidos (0/O, 1/l/I) para facilitar a digitacao.
CARACTERES_SENHA = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"


def gerar_senha_temporaria(tamanho=12):
    return "".join(secrets.choice(CARACTERES_SENHA) for _ in range(tamanho))


def listar_moradores(id_casa):
    with transacao() as cursor:
        return repo_moradores.listar_da_casa(cursor, id_casa)


def cadastrar_morador(id_casa, nome, email, perfil):
    """Vincula uma conta existente ou cria uma nova com senha temporaria.

    Tudo acontece na mesma transacao: se o vinculo falhar, a conta criada
    tambem e desfeita. A senha temporaria e devolvida somente aqui, uma vez;
    no banco fica apenas o hash.
    """
    perfil = validar_perfil(perfil)
    email = validar_email(email)

    senha_temporaria = None
    try:
        with transacao() as cursor:
            usuario = repo_usuarios.buscar_por_email(cursor, email, bloquear=True)
            if usuario:
                # Conta ja existe: so cria o vinculo, sem mexer em nome ou senha.
                id_usuario, nome = usuario["id_usuario"], usuario["nome"]
                if repo_moradores.participa(cursor, id_usuario, id_casa):
                    raise ValueError(f"{nome} ja participa desta casa.")
            else:
                try:
                    nome = validar_nome(nome)
                except ValueError:
                    raise ValueError("Esse e-mail ainda nao tem conta. Informe o nome "
                                     "completo (de 2 a 100 caracteres) para criar.")
                senha_temporaria = gerar_senha_temporaria()
                id_usuario = repo_usuarios.inserir(
                    cursor, nome, email, generate_password_hash(senha_temporaria),
                    trocar_senha=True,
                )
            repo_moradores.inserir(cursor, id_casa, id_usuario, perfil)
    except pymysql.err.IntegrityError:
        # Dois cadastros ao mesmo tempo: o UNIQUE do banco barra o segundo.
        raise ValueError("Esse morador acabou de ser cadastrado. Atualize a pagina.")

    return {"nome": nome, "email": email, "perfil": perfil,
            "senha_temporaria": senha_temporaria}


def _buscar_outro_morador(cursor, id_casa, id_morador, id_usuario_logado):
    morador = repo_moradores.buscar(cursor, id_morador, id_casa, bloquear=True)
    if not morador:
        raise ValueError("Morador nao encontrado.")
    if morador["id_usuario"] == id_usuario_logado:
        raise ValueError("Voce nao pode alterar o seu proprio acesso.")
    return morador


def mudar_perfil(id_casa, id_morador, perfil, id_usuario_logado):
    perfil = validar_perfil(perfil)
    with transacao() as cursor:
        _buscar_outro_morador(cursor, id_casa, id_morador, id_usuario_logado)
        repo_moradores.atualizar_perfil(cursor, id_morador, perfil)


def remover_morador(id_casa, id_morador, id_usuario_logado):
    """Tira o acesso a casa. A conta da pessoa continua existindo."""
    with transacao() as cursor:
        _buscar_outro_morador(cursor, id_casa, id_morador, id_usuario_logado)
        repo_moradores.excluir(cursor, id_morador)
