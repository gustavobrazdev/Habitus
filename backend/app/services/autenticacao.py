"""Cadastro de conta, login, troca de senha e acesso a casa aberta."""

import pymysql
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import transacao
from app.repositories import casas as repo_casas
from app.repositories import moradores as repo_moradores
from app.repositories import usuarios as repo_usuarios
from app.services.comodos import criar_comodos_iniciais
from app.validators.casas import validar_nome_casa, validar_opcao_comodos
from app.validators.usuarios import validar_email, validar_nome, validar_senha


def carregar_acesso(id_usuario, id_casa=None):
    """Dados da pessoa na casa aberta. Se ela nao participa mais dessa casa,
    usa a primeira casa em que participa. Devolve None se nao tiver nenhuma."""
    with transacao() as cursor:
        acesso = repo_moradores.buscar_acesso(cursor, id_usuario, id_casa) if id_casa else None
        return acesso or repo_moradores.buscar_primeiro_acesso(cursor, id_usuario)


def autenticar(email, senha):
    """Devolve o usuario se o e-mail e a senha estiverem corretos."""
    with transacao() as cursor:
        usuario = repo_usuarios.buscar_por_email(cursor, str(email or "").strip().lower())
    if usuario and check_password_hash(usuario["senha_hash"], senha or ""):
        return usuario
    return None


def cadastrar_conta(formulario):
    """Cria usuario, casa, vinculo de administrador e comodos iniciais juntos."""
    nome = validar_nome(formulario.get("nome"))
    email = validar_email(formulario.get("email"))
    senha = validar_senha(formulario.get("senha"), formulario.get("confirmacao"))
    nome_casa = validar_nome_casa(formulario.get("nome_casa"))
    opcao_comodos = validar_opcao_comodos(formulario.get("comodos_iniciais", "sugeridos"))

    try:
        with transacao() as cursor:
            id_usuario = repo_usuarios.inserir(cursor, nome, email, generate_password_hash(senha))
            id_casa = repo_casas.inserir(cursor, nome_casa)
            repo_moradores.inserir(cursor, id_casa, id_usuario, "administrador")
            criar_comodos_iniciais(cursor, id_casa, opcao_comodos)
    except pymysql.err.IntegrityError:
        raise ValueError("Esse e-mail ja esta cadastrado.")
    return {"id_usuario": id_usuario, "id_casa": id_casa, "opcao_comodos": opcao_comodos}


def trocar_senha_temporaria(id_usuario, senha, confirmacao):
    validar_senha(senha, confirmacao)
    with transacao() as cursor:
        usuario = repo_usuarios.buscar_por_id(cursor, id_usuario)
        if check_password_hash(usuario["senha_hash"], senha):
            raise ValueError("Escolha uma senha diferente da temporaria.")
        repo_usuarios.atualizar_senha(cursor, id_usuario, generate_password_hash(senha))
