"""Testes do gerenciamento de comodos sem depender de um MySQL instalado."""

import pytest

from apoio_banco import CursorFalso, entrar_como, transacao_com, usar_banco_falso
from app import criar_app
from app.models.comodo import Comodo
from app.services import comodos as servico


@pytest.fixture
def banco(monkeypatch):
    """Troca a conexao real do servico por um cursor falso configuravel."""
    def configurar(**kwargs):
        cursor = CursorFalso(**kwargs)
        monkeypatch.setattr(servico, "transacao", transacao_com(cursor))
        return cursor
    return configurar


EXISTENTES = [{"id_comodo": 1, "nome": "Sala"}, {"id_comodo": 2, "nome": "Quarto"}]


# ---------------------------------------------------------------- modelo

def test_nome_do_comodo_e_normalizado():
    assert Comodo("  Sala   de   estar ").nome == "Sala de estar"


@pytest.mark.parametrize("nome", ["", " ", "A", "x" * 81, None])
def test_nome_invalido_e_recusado(nome):
    with pytest.raises(ValueError):
        Comodo(nome)


def test_comparacao_ignora_maiusculas_e_espacos():
    assert Comodo("Sala").tem_mesmo_nome("SALA")
    assert Comodo("sala de estar").tem_mesmo_nome("  Sala  De Estar ")
    assert not Comodo("Sala").tem_mesmo_nome("Salas")


# ---------------------------------------------------------------- cadastro

def test_cadastra_comodo_com_nome_livre(banco):
    cursor = banco(todos=[EXISTENTES])
    comodo = servico.criar_comodo(7, "  Home   office ")
    assert comodo.nome == "Home office"
    insert = cursor.sql("INSERT INTO comodos")
    assert insert[0][1] == (7, "Home office")  # vinculado a casa correta


@pytest.mark.parametrize("nome", ["sala", "SALA", " Quarto "])
def test_nao_cadastra_nome_duplicado(banco, nome):
    cursor = banco(todos=[EXISTENTES])
    with pytest.raises(ValueError, match="Ja existe"):
        servico.criar_comodo(7, nome)
    assert not cursor.sql("INSERT")
    assert cursor.comandos[0][1] == (7,)  # so compara com comodos da mesma casa


def test_indice_unique_do_banco_tambem_e_tratado(banco):
    banco(todos=[[]], erro_no_insert=True)
    with pytest.raises(ValueError, match="Ja existe"):
        servico.criar_comodo(7, "Garagem")


def test_cadastro_inicial_sem_comodos():
    cursor = CursorFalso()
    assert servico.criar_comodos_iniciais(cursor, 3, "vazio") == []
    assert cursor.comandos == []


def test_cadastro_inicial_com_comodos_sugeridos():
    cursor = CursorFalso()
    assert servico.criar_comodos_iniciais(cursor, 3, "sugeridos") == ["Sala", "Quarto", "Cozinha"]
    assert [c[1] for c in cursor.sql("INSERT INTO comodos")] == [
        (3, "Sala"), (3, "Quarto"), (3, "Cozinha"),
    ]
    assert len(cursor.sql("INSERT INTO dispositivos")) == 2


def test_cadastro_inicial_com_opcao_invalida():
    from app.validators.casas import validar_opcao_comodos
    with pytest.raises(ValueError):
        validar_opcao_comodos("qualquer")


# ---------------------------------------------------------------- edicao

def test_renomeia_comodo(banco):
    cursor = banco(um=[{"id_comodo": 1, "nome": "Sala"}], todos=[EXISTENTES])
    assert servico.renomear_comodo(7, 1, "Sala de TV").nome == "Sala de TV"
    assert cursor.sql("UPDATE comodos")[0][1] == ("Sala de TV", 1, 7)


def test_pode_mudar_apenas_maiusculas_do_proprio_nome(banco):
    cursor = banco(um=[{"id_comodo": 1, "nome": "Sala"}], todos=[EXISTENTES])
    servico.renomear_comodo(7, 1, "SALA")
    assert cursor.sql("UPDATE comodos")


def test_nao_renomeia_para_nome_de_outro_comodo(banco):
    cursor = banco(um=[{"id_comodo": 1, "nome": "Sala"}], todos=[EXISTENTES])
    with pytest.raises(ValueError, match="Ja existe"):
        servico.renomear_comodo(7, 1, "quarto")
    assert not cursor.sql("UPDATE")


def test_nao_renomeia_comodo_de_outra_casa(banco):
    cursor = banco(um=[None])
    with pytest.raises(ValueError, match="nao encontrado"):
        servico.renomear_comodo(7, 99, "Garagem")
    assert cursor.comandos[0][1] == (99, 7)
    assert not cursor.sql("UPDATE")


# ---------------------------------------------------------------- exclusao

def test_exclui_comodo_sem_dispositivos(banco):
    cursor = banco(um=[{"id_comodo": 4, "nome": "Varanda"}, {"total": 0, "ativos": 0}])
    assert servico.excluir_comodo(7, 4) == "Varanda"
    assert cursor.sql("DELETE FROM comodos")[0][1] == (4, 7)


def test_nao_exclui_comodo_com_dispositivos(banco):
    cursor = banco(um=[{"id_comodo": 1, "nome": "Sala"}, {"total": 2, "ativos": 2}])
    with pytest.raises(ValueError, match="Transfira"):
        servico.excluir_comodo(7, 1)
    assert not cursor.sql("DELETE")


def test_nao_exclui_comodo_que_guarda_historico_de_dispositivo_removido(banco):
    cursor = banco(um=[{"id_comodo": 1, "nome": "Sala"}, {"total": 1, "ativos": 0}])
    with pytest.raises(ValueError, match="historico"):
        servico.excluir_comodo(7, 1)
    assert not cursor.sql("DELETE")


def test_nao_exclui_comodo_de_outra_casa(banco):
    cursor = banco(um=[None])
    with pytest.raises(ValueError, match="nao encontrado"):
        servico.excluir_comodo(7, 99)
    assert not cursor.sql("DELETE")


# ---------------------------------------------------------------- transferencia

DISPOSITIVO = {"id_dispositivo": 5, "nome": "Luz da sala", "id_comodo": 1, "nome_comodo": "Sala"}


def test_transfere_dispositivo_sem_perder_dados(banco):
    cursor = banco(um=[DISPOSITIVO, {"id_comodo": 2, "nome": "Quarto"}])
    assert servico.transferir_dispositivo(7, 5, 2, 9) == ("Luz da sala", "Quarto")

    update = cursor.sql("UPDATE")
    assert len(update) == 1
    # Somente o comodo muda: configuracoes, rotinas e historico ficam intactos.
    assert update[0] == ("UPDATE dispositivos SET id_comodo = %s WHERE id_dispositivo = %s", (2, 5))
    assert not cursor.sql("DELETE")
    assert not any("rotinas" in sql for sql, _ in cursor.comandos)
    historico = cursor.sql("INSERT INTO historico")
    assert historico[0][1] == (5, 9, "transferir_comodo", "Sala", "Quarto")


def test_nao_transfere_para_comodo_de_outra_casa(banco):
    cursor = banco(um=[DISPOSITIVO, None])
    with pytest.raises(ValueError, match="comodo desta casa"):
        servico.transferir_dispositivo(7, 5, 50, 9)
    assert not cursor.sql("UPDATE")


def test_nao_transfere_para_o_mesmo_comodo(banco):
    cursor = banco(um=[DISPOSITIVO, {"id_comodo": 1, "nome": "Sala"}])
    with pytest.raises(ValueError, match="ja esta"):
        servico.transferir_dispositivo(7, 5, 1, 9)
    assert not cursor.sql("UPDATE")


def test_nao_transfere_dispositivo_de_outra_casa(banco):
    cursor = banco(um=[None])
    with pytest.raises(ValueError, match="Dispositivo nao encontrado"):
        servico.transferir_dispositivo(7, 5, 2, 9)
    assert len(cursor.comandos) == 1


# ---------------------------------------------------------------- rotas e permissoes

@pytest.fixture
def app():
    return criar_app({"TESTING": True, "SECRET_KEY": "apenas-testes"})


ROTAS_DE_ADMINISTRADOR = [
    ("/casa/comodos", {"nome": "Garagem"}),
    ("/casa/comodos/1/renomear", {"nome": "Garagem"}),
    ("/casa/comodos/1/remover", {}),
    ("/dispositivos/5/transferir", {"id_comodo": "2"}),
]


@pytest.mark.parametrize("rota, dados", ROTAS_DE_ADMINISTRADOR)
def test_morador_comum_nao_gerencia_comodos(app, rota, dados, monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("O servico nao deveria ser chamado.")

    for nome in ("criar_comodo", "renomear_comodo", "excluir_comodo", "transferir_dispositivo"):
        monkeypatch.setattr(servico, nome, proibido)
    monkeypatch.setattr("app.routes.dispositivos.transferir_dispositivo", proibido)

    cliente, sessao = entrar_como(app, "comum")
    with sessao:
        resposta = cliente.post(rota, data={**dados, "csrf_token": "token-teste"})
    assert resposta.status_code == 403


def test_visitante_sem_login_e_redirecionado(app):
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["csrf_token"] = "token-teste"
    resposta = cliente.post("/casa/comodos/1/remover", data={"csrf_token": "token-teste"})
    assert resposta.status_code == 302
    assert "/entrar" in resposta.location


def test_administrador_renomeia_na_casa_aberta(app, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        servico, "renomear_comodo",
        lambda *args: chamadas.append(args) or Comodo(args[2]),
    )
    cliente, sessao = entrar_como(app, "administrador")
    with sessao:
        resposta = cliente.post(
            "/casa/comodos/3/renomear", data={"nome": "Escritorio", "csrf_token": "token-teste"}
        )
    assert resposta.status_code == 302
    assert chamadas == [(7, 3, "Escritorio")]


def test_administrador_transfere_dispositivo(app, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "app.routes.dispositivos.transferir_dispositivo",
        lambda *args: chamadas.append(args) or ("Luz", "Quarto"),
    )
    cliente, sessao = entrar_como(app, "administrador")
    with sessao:
        resposta = cliente.post(
            "/dispositivos/5/transferir", data={"id_comodo": "2", "csrf_token": "token-teste"}
        )
        invalida = cliente.post(
            "/dispositivos/5/transferir", data={"id_comodo": "abc", "csrf_token": "token-teste"}
        )
    assert resposta.status_code == invalida.status_code == 302
    assert chamadas == [(7, 5, 2, 9)]  # o valor invalido nao chega ao servico


def test_tela_de_cadastro_oferece_as_opcoes_de_comodos(app):
    texto = app.test_client().get("/cadastro").get_data(as_text=True)
    assert 'value="sugeridos"' in texto and 'value="vazio"' in texto


def test_cadastro_rejeita_opcao_de_comodos_invalida(app, monkeypatch):
    def sem_banco():
        raise AssertionError("Nao deveria acessar o banco.")

    monkeypatch.setattr("app.services.autenticacao.transacao", sem_banco)
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["csrf_token"] = "token-teste"
    resposta = cliente.post("/cadastro", data={
        "nome": "Ana", "email": "ana@exemplo.com", "nome_casa": "Casa da Ana",
        "senha": "12345678", "confirmacao": "12345678",
        "comodos_iniciais": "outra", "csrf_token": "token-teste",
    })
    assert resposta.status_code == 200
    assert "Escolha como deseja comecar" in resposta.get_data(as_text=True)


def test_cadastro_sem_comodos_nao_cria_ambientes(app, monkeypatch):
    import app.services.autenticacao as autenticacao
    cursor = usar_banco_falso(monkeypatch, autenticacao)
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao["csrf_token"] = "token-teste"
    resposta = cliente.post("/cadastro", data={
        "nome": "Ana", "email": "ana@exemplo.com", "nome_casa": "Casa da Ana",
        "senha": "12345678", "confirmacao": "12345678",
        "comodos_iniciais": "vazio", "csrf_token": "token-teste",
    })
    assert resposta.status_code == 302
    assert not cursor.sql("INSERT INTO comodos")
    assert not cursor.sql("INSERT INTO dispositivos")
    assert len(cursor.sql("INSERT INTO moradores")) == 1
