"""Validacoes de usuarios: nome, e-mail, senha e perfil."""

import re

from app.models.usuario import Usuario
from app.validators.campos import opcao, texto

TAMANHO_MINIMO_SENHA = 8


def validar_nome(nome):
    return texto(nome, "O nome", 2, 100)


def validar_email(email):
    email = str(email or "").strip().lower()
    if len(email) > 150 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Informe um e-mail valido.")
    return email


def validar_senha(senha, confirmacao):
    if len(senha or "") < TAMANHO_MINIMO_SENHA:
        raise ValueError(f"A senha deve ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres.")
    if senha != confirmacao:
        raise ValueError("As senhas nao conferem.")
    return senha


def validar_perfil(perfil):
    return opcao(perfil, Usuario.PERFIS, "Escolha uma permissao valida.")
