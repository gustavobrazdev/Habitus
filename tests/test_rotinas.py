"""Cadastro, exibicao e edicao de rotinas."""

from datetime import timedelta
from decimal import Decimal

import pytest

from apoio_banco import CursorFalso, entrar_como, transacao_com, usar_banco_falso
from app import criar_app
from app.models.rotina import Rotina, dias_para_texto, formatar_horario
from app.services import rotinas as servico


LUZ = {"id_dispositivo": 5, "tipo": "luz", "ligado": 0, "brilho": 80}
AR = {"id_dispositivo": 6, "tipo": "ar_condicionado", "ligado": 0, "temperatura": 22}
VENTILADOR = {"id_dispositivo": 8, "tipo": "ventilador", "ligado": 0, "intensidade": 50}


def dados_rotina(**mudancas):
    dados = {"id_dispositivo": "5", "nome": "Luz da noite", "acao": "ajustar_brilho",
             "valor": "75", "horario": "19:30", "dias": [str(dia) for dia in range(7)]}
    dados.update(mudancas)
    return dados


@pytest.fixture
def banco(monkeypatch):
    def configurar(**kwargs):
        cursor = CursorFalso(**kwargs)
        monkeypatch.setattr(servico, "transacao", transacao_com(cursor))
        return cursor
    return configurar


# ---------------------------------------------------------------- exibicao

def test_cartao_mostra_valor_com_unidade_como_vem_do_mysql():
    # O MySQL devolve TIME como timedelta e DECIMAL(5,1) como Decimal.
    linha = {"id_rotina": 1, "nome": "Luz", "acao": "ajustar_brilho", "valor": Decimal("75.0"),
             "horario": timedelta(hours=7, minutes=5), "dias_semana": "0,2,4", "ativa": 1}
    rotina = Rotina(linha)
    assert rotina.horario == "07:05"
    assert rotina.valor_texto == "75%"
    assert rotina.acao_texto == "Ajustar brilho para 75%"
    assert rotina.dias_texto == "Seg, Qua, Sex"
    assert rotina.ativa


@pytest.mark.parametrize("acao, valor, texto", [
    ("ajustar_temperatura", Decimal("23.0"), "Ajustar temperatura para 23 °C"),
    ("ajustar_temperatura", Decimal("22.5"), "Ajustar temperatura para 22,5 °C"),
    ("ajustar_intensidade", Decimal("40.0"), "Ajustar intensidade para 40%"),
    ("ligar", None, "Ligar"),
    ("desligar", None, "Desligar"),
])
def test_descricao_da_acao(acao, valor, texto):
    rotina = Rotina({"acao": acao, "valor": valor, "horario": "19:00:00",
                     "dias_semana": "todos", "ativa": 0})
    assert rotina.acao_texto == texto
    assert rotina.dias_texto == "Todos os dias"
    assert not rotina.ativa


def test_valor_volta_para_o_formulario_de_edicao():
    assert Rotina({"acao": "ajustar_brilho", "valor": Decimal("70.0"), "horario": "08:00"}).valor_formulario == "70"
    assert Rotina({"acao": "ajustar_temperatura", "valor": Decimal("22.5"), "horario": "08:00"}).valor_formulario == "22.5"


def test_horario_e_dias():
    assert formatar_horario(timedelta(hours=19)) == "19:00"
    assert formatar_horario("08:15:00") == "08:15"
    assert dias_para_texto({"0", "1", "2", "3", "4", "5", "6"}) == "todos"
    assert dias_para_texto({"4", "0", "2"}) == "0,2,4"


# ---------------------------------------------------------------- salvar

@pytest.mark.parametrize("dispositivo, acao, valor, esperado", [
    (LUZ, "ajustar_brilho", "75", 75),
    (AR, "ajustar_temperatura", "23,5", 23.5),
    (VENTILADOR, "ajustar_intensidade", "40", 40),
])
def test_cria_rotina_com_ajuste_sem_executar_agora(banco, dispositivo, acao, valor, esperado):
    cursor = banco(um=[dispositivo])
    servico.salvar_rotina(7, dados_rotina(id_dispositivo=dispositivo["id_dispositivo"],
                                          acao=acao, valor=valor))
    insert = cursor.sql("INSERT INTO rotinas")
    assert len(insert) == 1
    assert insert[0][1] == (dispositivo["id_dispositivo"], "Luz da noite", acao, esperado,
                            "19:30", "todos")
    # Nada muda no dispositivo e nada vai para o historico no momento do cadastro.
    assert not cursor.sql("UPDATE")
    assert not cursor.sql("INSERT INTO historico")


def test_ligar_e_desligar_nao_guardam_valor(banco):
    cursor = banco(um=[LUZ])
    servico.salvar_rotina(7, dados_rotina(acao="ligar", valor="50"))
    assert cursor.sql("INSERT INTO rotinas")[0][1][3] is None


@pytest.mark.parametrize("dispositivo, acao, valor", [
    (LUZ, "ajustar_brilho", "150"),
    (LUZ, "ajustar_brilho", ""),
    (LUZ, "ajustar_temperatura", "22"),  # acao incompativel com luz
    (AR, "ajustar_temperatura", "35"),
])
def test_valor_ou_acao_invalidos_nao_salvam(banco, dispositivo, acao, valor):
    cursor = banco(um=[dispositivo])
    with pytest.raises(ValueError):
        servico.salvar_rotina(7, dados_rotina(acao=acao, valor=valor))
    assert not cursor.sql("INSERT") and not cursor.sql("UPDATE")


def test_nao_usa_dispositivo_de_outra_casa(banco):
    cursor = banco(um=[None])
    with pytest.raises(ValueError, match="Dispositivo nao encontrado"):
        servico.salvar_rotina(7, dados_rotina())
    assert cursor.comandos[0][1] == [5, 7]  # busca o dispositivo somente na casa 7


def test_edicao_atualiza_a_mesma_rotina(banco):
    cursor = banco(um=[AR, {"id_rotina": 3}])
    servico.salvar_rotina(7, dados_rotina(id_dispositivo=6, acao="ajustar_temperatura",
                                          valor="24", horario="06:45", dias=["0", "1"]), 3)
    assert not cursor.sql("INSERT")
    update = cursor.sql("UPDATE rotinas")
    assert len(update) == 1
    assert update[0][1] == (6, "Luz da noite", "ajustar_temperatura", 24.0, "06:45", "0,1", 3)


def test_nao_edita_rotina_de_outra_casa(banco):
    cursor = banco(um=[LUZ, None])
    with pytest.raises(ValueError, match="Rotina nao encontrada"):
        servico.salvar_rotina(7, dados_rotina(), 99)
    assert not cursor.sql("UPDATE")


# ---------------------------------------------------------------- rotas

@pytest.fixture
def app():
    return criar_app({"TESTING": True, "SECRET_KEY": "apenas-testes"})


LINHA_SALVA = {
    "id_rotina": 3, "id_dispositivo": 5, "nome": "Luz da noite", "acao": "ajustar_brilho",
    "valor": Decimal("75.0"), "horario": timedelta(hours=19, minutes=30),
    "dias_semana": "0,1,2,3,4", "ativa": 1, "nome_dispositivo": "Luz da sala",
    "nome_comodo": "Sala", "tipo": "luz",
}
DISPOSITIVOS = [{"id_dispositivo": 5, "nome": "Luz da sala", "tipo": "luz", "nome_comodo": "Sala"}]


def banco_da_pagina(monkeypatch, um=()):
    """Respostas para listar as rotinas e os dispositivos da pagina."""
    return usar_banco_falso(monkeypatch, servico, um=list(um),
                            todos=[[dict(LINHA_SALVA)], [dict(d) for d in DISPOSITIVOS]])


def test_lista_mostra_os_dados_salvos_depois_de_atualizar(app, monkeypatch):
    banco_da_pagina(monkeypatch)
    cliente, sessao = entrar_como(app, "comum")
    with sessao:
        texto = cliente.get("/rotinas").get_data(as_text=True)
    for trecho in ("Luz da noite", "Luz da sala", "Ajustar brilho para 75%",
                   "19:30", "Segunda a sexta", "Ativa"):
        assert trecho in texto
    assert "Editar" not in texto  # morador comum nao ve o botao


def test_editar_abre_formulario_preenchido(app, monkeypatch):
    banco_da_pagina(monkeypatch, um=[LINHA_SALVA])
    cliente, sessao = entrar_como(app, "administrador")
    with sessao:
        texto = cliente.get("/rotinas/3/editar").get_data(as_text=True)
    assert "Editar rotina" in texto and "Cancelar edição" in texto
    assert 'action="/rotinas/3/editar"' in texto
    assert 'value="Luz da noite"' in texto
    assert 'value="19:30"' in texto
    assert 'data-salvo="75"' in texto
    assert '<option value="ajustar_brilho" selected>' in texto
    assert 'value="4" checked' in texto and 'value="5" >' in texto


def test_envio_da_edicao_chama_o_servico_com_o_id(app, monkeypatch):
    chamadas = []
    monkeypatch.setattr(servico, "salvar_rotina", lambda *a: chamadas.append(a))
    cliente, sessao = entrar_como(app, "administrador")
    with sessao:
        resposta = cliente.post("/rotinas/3/editar", data={
            "nome": "Luz  da noite", "id_dispositivo": "5", "acao": "ajustar_brilho",
            "valor": "60", "horario": "20:00", "dias": ["0", "6"], "csrf_token": "token-teste",
        })
    assert resposta.status_code == 302
    id_casa, formulario, id_rotina = chamadas[0]
    assert (id_casa, id_rotina) == (7, 3)
    assert formulario["id_dispositivo"] == 5 and formulario["valor"] == "60"
    assert formulario["dias"] == {"0", "6"}


def test_erro_mantem_o_que_foi_digitado(app, monkeypatch):
    banco_da_pagina(monkeypatch)
    cliente, sessao = entrar_como(app, "administrador")
    with sessao:
        resposta = cliente.post("/rotinas", data={
            "nome": "Minha rotina", "id_dispositivo": "5", "acao": "ligar",
            "horario": "20:00", "csrf_token": "token-teste",  # sem dias
        })
    texto = resposta.get_data(as_text=True)
    assert resposta.status_code == 400
    assert "Selecione pelo menos um dia" in texto
    assert 'value="Minha rotina"' in texto


@pytest.mark.parametrize("metodo, rota", [
    ("get", "/rotinas/3/editar"),
    ("post", "/rotinas/3/editar"),
    ("post", "/rotinas"),
])
def test_morador_comum_nao_cria_nem_edita_rotinas(app, monkeypatch, metodo, rota):
    def proibido(*a):
        raise AssertionError("Nao deveria salvar.")
    monkeypatch.setattr(servico, "salvar_rotina", proibido)
    cliente, sessao = entrar_como(app, "comum")
    with sessao:
        resposta = getattr(cliente, metodo)(rota, data={"csrf_token": "token-teste"})
    assert resposta.status_code == 403
