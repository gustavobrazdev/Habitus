"""Cadastro de moradores, senha temporaria e troca obrigatoria no primeiro acesso."""

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from apoio_banco import entrar_como, transacao_com, usar_banco_falso
from app import criar_app
from app.services import autenticacao
from app.services import moradores as servico


@pytest.fixture
def app():
    return criar_app({"TESTING": True, "SECRET_KEY": "apenas-testes"})


@pytest.fixture
def banco(monkeypatch):
    def configurar(**kwargs):
        from apoio_banco import CursorFalso
        cursor = CursorFalso(**kwargs)
        monkeypatch.setattr(servico, "transacao", transacao_com(cursor))
        return cursor
    return configurar


# ---------------------------------------------------------------- servico

def test_senha_temporaria_e_aleatoria_e_legivel():
    senhas = {servico.gerar_senha_temporaria() for _ in range(50)}
    assert len(senhas) == 50
    for senha in senhas:
        assert len(senha) == 12
        assert not set(senha) & set("0O1lI")


def test_cadastra_novo_morador_com_senha_temporaria(banco):
    cursor = banco(um=[None])  # e-mail ainda nao existe
    resultado = servico.cadastrar_morador(7, "  Carlos   Souza ", "Carlos@Exemplo.com ", "comum")

    senha = resultado["senha_temporaria"]
    assert resultado["nome"] == "Carlos Souza"
    usuario = cursor.sql("INSERT INTO usuarios")[0][1]
    assert usuario[:2] == ("Carlos Souza", "carlos@exemplo.com")
    assert senha not in usuario  # somente o hash vai para o banco
    assert check_password_hash(usuario[2], senha)
    assert "trocar_senha" in cursor.sql("INSERT INTO usuarios")[0][0]
    assert cursor.sql("INSERT INTO moradores")[0][1] == (7, cursor.lastrowid - 1, "comum")


def test_vincula_conta_existente_sem_mudar_senha(banco):
    cursor = banco(um=[{"id_usuario": 4, "nome": "Bia"}, None])
    resultado = servico.cadastrar_morador(7, "", "bia@exemplo.com", "administrador")

    assert resultado["senha_temporaria"] is None
    assert resultado["nome"] == "Bia"
    assert not cursor.sql("INSERT INTO usuarios")
    assert not cursor.sql("UPDATE")
    assert cursor.sql("INSERT INTO moradores")[0][1] == (7, 4, "administrador")


def test_nao_vincula_quem_ja_participa_da_casa(banco):
    cursor = banco(um=[{"id_usuario": 4, "nome": "Bia"}, {"1": 1}])
    with pytest.raises(ValueError, match="ja participa"):
        servico.cadastrar_morador(7, "", "bia@exemplo.com", "comum")
    assert not cursor.sql("INSERT")


def test_cadastro_simultaneo_vira_mensagem_e_desfaz_a_transacao(banco):
    # O IntegrityError sai de dentro do "with transacao()", que faz o rollback.
    banco(um=[None], erro_no_insert=True)
    with pytest.raises(ValueError, match="acabou de ser cadastrado"):
        servico.cadastrar_morador(7, "Carlos", "carlos@exemplo.com", "comum")


@pytest.mark.parametrize("nome, email, perfil, mensagem", [
    ("Carlos", "email-invalido", "comum", "e-mail"),
    ("Carlos", "carlos@exemplo.com", "dono", "permissao"),
])
def test_dados_invalidos_nem_acessam_o_banco(monkeypatch, nome, email, perfil, mensagem):
    def sem_banco():
        raise AssertionError("Nao deveria acessar o banco.")
    monkeypatch.setattr(servico, "transacao", sem_banco)
    with pytest.raises(ValueError, match=mensagem):
        servico.cadastrar_morador(7, nome, email, perfil)


def test_nome_e_obrigatorio_para_conta_nova(banco):
    cursor = banco(um=[None])
    with pytest.raises(ValueError, match="nome completo"):
        servico.cadastrar_morador(7, "", "novo@exemplo.com", "comum")
    assert not cursor.sql("INSERT")


# ---------------------------------------------------------------- rotas

def test_administrador_ve_a_senha_temporaria_uma_unica_vez(app, monkeypatch):
    monkeypatch.setattr(servico, "cadastrar_morador", lambda *a: {
        "nome": "Carlos", "email": "carlos@exemplo.com", "perfil": "comum",
        "senha_temporaria": "SenhaTemp234",
    })
    monkeypatch.setattr(servico, "listar_moradores", lambda *a: [])
    monkeypatch.setattr("app.services.comodos.listar_comodos", lambda *a: [])
    monkeypatch.setattr("app.routes.casas.casas_do_usuario", lambda *a: [])
    cliente, sessao = entrar_como(app, "administrador")
    with sessao:
        resposta = cliente.post("/casa/moradores", data={
            "nome": "Carlos", "email": "carlos@exemplo.com", "perfil": "comum",
            "csrf_token": "token-teste",
        })
        depois = cliente.get("/casa")
    assert resposta.status_code == 200
    assert "SenhaTemp234" in resposta.get_data(as_text=True)
    assert resposta.headers["Cache-Control"] == "no-store"
    assert "SenhaTemp234" not in depois.get_data(as_text=True)
    with cliente.session_transaction() as dados_sessao:
        assert "SenhaTemp234" not in str(dict(dados_sessao))


def test_morador_comum_nao_cadastra_moradores(app, monkeypatch):
    def proibido(*args):
        raise AssertionError("Nao deveria cadastrar.")
    monkeypatch.setattr(servico, "cadastrar_morador", proibido)
    cliente, sessao = entrar_como(app, "comum")
    with sessao:
        resposta = cliente.post("/casa/moradores", data={
            "email": "x@exemplo.com", "perfil": "administrador", "csrf_token": "token-teste",
        })
    assert resposta.status_code == 403


def test_login_com_senha_temporaria_exige_troca(app, monkeypatch):
    usuario = {"id_usuario": 9, "senha_hash": generate_password_hash("Temporaria23"),
               "trocar_senha": 1}
    usar_banco_falso(monkeypatch, autenticacao, um=[usuario])
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["csrf_token"] = "token-teste"
    resposta = cliente.post("/entrar", data={
        "email": "carlos@exemplo.com", "senha": "Temporaria23", "csrf_token": "token-teste",
    })
    assert resposta.status_code == 302
    assert resposta.location.endswith("/trocar-senha")


def test_login_de_conta_antiga_continua_normal(app, monkeypatch):
    # Linha sem a coluna trocar_senha (banco antes da migracao).
    usuario = {"id_usuario": 9, "senha_hash": generate_password_hash("SenhaNormal1")}
    usar_banco_falso(monkeypatch, autenticacao, um=[usuario])
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["csrf_token"] = "token-teste"
    resposta = cliente.post("/entrar", data={
        "email": "ana@exemplo.com", "senha": "SenhaNormal1", "csrf_token": "token-teste",
    })
    assert resposta.location.endswith("/painel")


def test_sem_trocar_a_senha_nao_acessa_outras_paginas(app):
    cliente, sessao = entrar_como(app, "comum", trocar_senha=True)
    with sessao:
        for pagina in ("/painel", "/dispositivos", "/casa", "/rotinas"):
            resposta = cliente.get(pagina)
            assert resposta.status_code == 302
            assert resposta.location.endswith("/trocar-senha")
        tela = cliente.get("/trocar-senha")
    assert tela.status_code == 200
    assert "Crie sua senha" in tela.get_data(as_text=True)


def test_troca_de_senha_grava_hash_e_libera_o_sistema(app, monkeypatch):
    temporaria = {"senha_hash": generate_password_hash("Temporaria23")}
    cursor = usar_banco_falso(monkeypatch, autenticacao, um=[temporaria, temporaria])
    cliente, sessao = entrar_como(app, "comum", trocar_senha=True)
    with sessao:
        igual = cliente.post("/trocar-senha", data={
            "senha": "Temporaria23", "confirmacao": "Temporaria23", "csrf_token": "token-teste",
        })
        assert "diferente da temporaria" in igual.get_data(as_text=True)
        assert not cursor.sql("UPDATE")

        resposta = cliente.post("/trocar-senha", data={
            "senha": "MinhaSenha2050", "confirmacao": "MinhaSenha2050", "csrf_token": "token-teste",
        })
    assert resposta.location.endswith("/painel")
    sql, valores = cursor.sql("UPDATE usuarios")[0]
    assert "trocar_senha = 0" in sql
    assert check_password_hash(valores[0], "MinhaSenha2050") and valores[1] == 9
    with cliente.session_transaction() as dados_sessao:
        assert "trocar_senha" not in dados_sessao
