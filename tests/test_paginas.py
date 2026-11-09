"""Testes simples das paginas sem precisar acessar o MySQL."""

from unittest.mock import patch

import pytest

from app import criar_app


@pytest.fixture
def cliente():
    app = criar_app({"TESTING": True, "SECRET_KEY": "apenas-testes"})
    return app.test_client()


def test_tela_de_login(cliente):
    resposta = cliente.get("/entrar")
    assert resposta.status_code == 200
    assert "Bem-vindo de volta" in resposta.get_data(as_text=True)


def test_tela_de_cadastro(cliente):
    resposta = cliente.get("/cadastro")
    assert resposta.status_code == 200
    assert "Crie sua casa" in resposta.get_data(as_text=True)


def test_painel_exige_login(cliente):
    resposta = cliente.get("/painel")
    assert resposta.status_code == 302
    assert "/entrar" in resposta.location


def test_post_sem_token_nao_e_aceito(cliente):
    resposta = cliente.post("/cadastro", data={"nome": "Teste"})
    assert resposta.status_code == 400


def test_morador_comum_nao_pode_adicionar_comodo(cliente):
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = 9
        sessao["casa_id"] = 3
        sessao["csrf_token"] = "token-teste"
    morador = {"id_usuario": 9, "nome": "Teste", "perfil": "comum", "id_casa": 3, "nome_casa": "Casa"}
    with patch("app.carregar_acesso", return_value=morador):
        resposta = cliente.post("/casa/comodos", data={"nome": "Teste", "csrf_token": "token-teste"})
    assert resposta.status_code == 403


# ---------------------------------------------------------------- camadas integradas
# Rota -> servico -> repositorio -> banco falso (sem MySQL).

from datetime import datetime
from decimal import Decimal

from werkzeug.security import check_password_hash, generate_password_hash

from apoio_banco import entrar_como, usar_banco_falso
from app.services import autenticacao, casas, dispositivos

LUZ = {"id_dispositivo": 5, "id_comodo": 1, "nome": "Luz da sala", "tipo": "luz", "ligado": 1,
       "brilho": 80, "temperatura": None, "intensidade": None, "nome_comodo": "Sala"}
AR = {"id_dispositivo": 6, "id_comodo": 2, "nome": "Ar do quarto", "tipo": "ar_condicionado",
      "ligado": 0, "brilho": None, "temperatura": Decimal("22.0"), "intensidade": None,
      "nome_comodo": "Quarto"}
COMODOS = [{"id_comodo": 1, "nome": "Sala"}, {"id_comodo": 2, "nome": "Quarto"}]


def test_painel_agrupa_dispositivos_por_comodo(monkeypatch):
    evento = {"dispositivo": "Luz da sala", "acao": "ligar", "usuario": None,
              "data_acao": datetime(2026, 11, 4, 19, 0)}
    usar_banco_falso(monkeypatch, casas, todos=[COMODOS, [LUZ, AR], [evento]],
                     um=[{"total": 3}])
    app = criar_app({"TESTING": True})
    cliente, sessao = entrar_como(app, "comum")
    with sessao:
        texto = cliente.get("/painel").get_data(as_text=True)
    assert "Luz da sala" in texto and "Ar do quarto" in texto
    assert "Automação" in texto  # evento sem usuario veio de uma rotina


def test_pagina_de_dispositivos_usa_limites_das_classes(monkeypatch):
    usar_banco_falso(monkeypatch, dispositivos, todos=[[LUZ, AR], COMODOS])
    app = criar_app({"TESTING": True})
    cliente, sessao = entrar_como(app, "administrador")
    with sessao:
        texto = cliente.get("/dispositivos").get_data(as_text=True)
    assert 'min="16" max="30" step="0.5"' in texto      # Climatizador.ajuste
    assert "22 °C" in texto                              # filtro |numero
    assert 'value="ajustar_brilho"' in texto and "Salvar brilho" in texto
    assert "Mover para" in texto


def test_cadastro_e_login_passando_pelas_camadas(monkeypatch):
    app = criar_app({"TESTING": True})
    cursor = usar_banco_falso(monkeypatch, autenticacao)
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["csrf_token"] = "t"
    resposta = cliente.post("/cadastro", data={
        "nome": "Ana", "email": "Ana@Exemplo.com", "nome_casa": "Casa da Ana",
        "senha": "senha1234", "confirmacao": "senha1234", "csrf_token": "t",
    })
    assert resposta.status_code == 302 and resposta.location.endswith("/painel")
    usuario = cursor.sql("INSERT INTO usuarios")[0][1]
    assert usuario[1] == "ana@exemplo.com" and check_password_hash(usuario[2], "senha1234")
    assert cursor.sql("INSERT INTO moradores")[0][1][2] == "administrador"
    assert len(cursor.sql("INSERT INTO comodos")) == 3  # opcao padrao: sugeridos

    usar_banco_falso(monkeypatch, autenticacao, um=[
        {"id_usuario": 1, "senha_hash": generate_password_hash("senha1234")}])
    with cliente.session_transaction() as sessao:
        sessao.clear()
        sessao["csrf_token"] = "t"
    errado = cliente.post("/entrar", data={"email": "ana@exemplo.com", "senha": "outra123", "csrf_token": "t"})
    assert "E-mail ou senha incorretos" in errado.get_data(as_text=True)


def test_sair_limpa_a_sessao():
    app = criar_app({"TESTING": True})
    cliente, sessao = entrar_como(app, "comum")
    with sessao:
        cliente.post("/sair", data={"csrf_token": "token-teste"})
    with cliente.session_transaction() as dados:
        assert "usuario_id" not in dados
