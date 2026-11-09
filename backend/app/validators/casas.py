"""Validacoes de casas e comodos."""

from app.validators.campos import opcao, texto

OPCOES_COMODOS_INICIAIS = ("sugeridos", "vazio")


def validar_nome_casa(nome):
    return texto(nome, "O nome da casa", 2, 100)


def validar_nome_comodo(nome):
    return texto(nome, "O nome do comodo", 2, 80)


def validar_opcao_comodos(valor):
    return opcao(valor, OPCOES_COMODOS_INICIAIS, "Escolha como deseja comecar os comodos da casa.")
