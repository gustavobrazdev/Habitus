"""Servicos de dispositivos e do executor de rotinas, sem depender de um MySQL instalado."""

from datetime import datetime, timedelta

import pytest

from apoio_banco import usar_banco_falso
from app import criar_app
from app import database
from app.services import dispositivos as servico_dispositivos
from app.services import rotinas as servico_rotinas

LUZ = {"id_dispositivo": 5, "tipo": "luz", "ligado": 0, "brilho": 80}
AR = {"id_dispositivo": 6, "tipo": "ar_condicionado", "ligado": 1, "temperatura": 22}


# ---------------------------------------------------------------- transacao

class ConexaoFalsa:
    def __init__(self, falhar=False):
        self.eventos = []

    def cursor(self):
        conexao = self

        class Cursor:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def execute(self, sql, valores=None):
                conexao.eventos.append("execute")
        return Cursor()

    def commit(self):
        self.eventos.append("commit")

    def rollback(self):
        self.eventos.append("rollback")

    def close(self):
        self.eventos.append("close")


def test_transacao_confirma_ou_desfaz_tudo(monkeypatch):
    conexao = ConexaoFalsa()
    monkeypatch.setattr(database, "conectar", lambda: conexao)
    with database.transacao() as cursor:
        cursor.execute("UPDATE ...")
    assert conexao.eventos == ["execute", "commit", "close"]

    conexao = ConexaoFalsa()
    monkeypatch.setattr(database, "conectar", lambda: conexao)
    with pytest.raises(ValueError):
        with database.transacao() as cursor:
            cursor.execute("UPDATE ...")
            raise ValueError("falhou no meio")
    assert conexao.eventos == ["execute", "rollback", "close"]


# ---------------------------------------------------------------- dispositivos

def test_alteracao_grava_estado_e_historico(monkeypatch):
    cursor = usar_banco_falso(monkeypatch, servico_dispositivos, um=[dict(LUZ)])

    resultado = servico_dispositivos.alterar_dispositivo(5, 2, 9, "ajustar_brilho", "45")
    assert resultado == {"campo": "brilho", "antes": 80, "depois": 45}
    assert len(cursor.comandos) == 3  # SELECT, UPDATE, INSERT historico
    assert "FOR UPDATE" in cursor.comandos[0][0]
    assert "SET brilho = %s" in cursor.comandos[1][0]
    assert cursor.comandos[1][1] == (45, 5)
    assert "INSERT INTO historico" in cursor.comandos[2][0]
    assert cursor.comandos[2][1] == (5, 9, "ajustar_brilho", "80", "45")


def test_controle_de_temperatura(monkeypatch):
    cursor = usar_banco_falso(monkeypatch, servico_dispositivos, um=[dict(AR)])
    resultado = servico_dispositivos.alterar_dispositivo(6, 2, 9, "ajustar_temperatura", "24,5")
    assert resultado == {"campo": "temperatura", "antes": 22, "depois": 24.5}
    assert cursor.sql("UPDATE dispositivos SET temperatura")[0][1] == (24.5, 6)


def test_valor_invalido_nao_grava_no_banco(monkeypatch):
    cursor = usar_banco_falso(monkeypatch, servico_dispositivos, um=[dict(LUZ)])
    with pytest.raises(ValueError):
        servico_dispositivos.alterar_dispositivo(5, 2, 9, "ajustar_brilho", "200")
    assert len(cursor.comandos) == 1  # somente SELECT


def test_dispositivo_de_outra_casa_nao_e_controlado(monkeypatch):
    cursor = usar_banco_falso(monkeypatch, servico_dispositivos, um=[None])
    with pytest.raises(ValueError, match="nao encontrado"):
        servico_dispositivos.alterar_dispositivo(5, 2, 9, "ligar")
    assert cursor.comandos[0][1] == [5, 2]


def test_cadastra_dispositivo_com_configuracao_da_classe(monkeypatch):
    cursor = usar_banco_falso(monkeypatch, servico_dispositivos, um=[{"id_comodo": 3}])
    servico_dispositivos.cadastrar_dispositivo(7, " Ar  do escritorio ", "aquecedor", "3")
    assert cursor.sql("INSERT INTO dispositivos")[0][1] == (3, "Ar do escritorio", "aquecedor", None, 25, None)


@pytest.mark.parametrize("nome, tipo, comodo, mensagem", [
    ("A", "luz", "3", "nome do dispositivo"),
    ("Luz", "geladeira", "3", "tipo"),
    ("Luz", "luz", "abc", "comodo"),
])
def test_cadastro_de_dispositivo_invalido(monkeypatch, nome, tipo, comodo, mensagem):
    cursor = usar_banco_falso(monkeypatch, servico_dispositivos)
    with pytest.raises(ValueError, match=mensagem):
        servico_dispositivos.cadastrar_dispositivo(7, nome, tipo, comodo)
    assert not cursor.comandos


def test_nao_cadastra_em_comodo_de_outra_casa(monkeypatch):
    cursor = usar_banco_falso(monkeypatch, servico_dispositivos, um=[None])
    with pytest.raises(ValueError, match="comodo da sua casa"):
        servico_dispositivos.cadastrar_dispositivo(7, "Luz", "luz", "99")
    assert not cursor.sql("INSERT")


def test_remover_dispositivo_preserva_historico(monkeypatch):
    cursor = usar_banco_falso(monkeypatch, servico_dispositivos)
    servico_dispositivos.remover_dispositivo(7, 5)
    assert "SET d.ativo = 0" in cursor.comandos[0][0]
    assert cursor.sql("UPDATE rotinas SET ativa = 0")
    assert not cursor.sql("DELETE")


# ---------------------------------------------------------------- executor de rotinas

def rotina_das_19h(**mudancas):
    rotina = {
        "id_rotina": 4, "id_dispositivo": 5, "nome": "Ligar luz da sala",
        "horario": timedelta(hours=19), "dias_semana": "todos",
        "ativa": True, "ultima_execucao": None, "acao": "ligar", "valor": None,
    }
    rotina.update(mudancas)
    return rotina


def test_rotina_executa_e_registra_historico(monkeypatch):
    agora = datetime(2026, 11, 4, 19, 0, 10)
    rotina = rotina_das_19h()
    cursor = usar_banco_falso(monkeypatch, servico_rotinas,
                              todos=[[rotina]], um=[rotina, dict(LUZ)])

    assert servico_rotinas.executar_pendentes(agora) == (["Ligar luz da sala"], [])
    comandos = cursor.comandos[1:]  # o primeiro e a listagem das rotinas ativas
    assert len(comandos) == 5  # SELECT rotina, SELECT dispositivo, UPDATE, INSERT, UPDATE rotina
    assert "INSERT INTO historico" in comandos[3][0]
    assert comandos[3][1][1] is None  # automacao: sem usuario
    assert comandos[4] == ("UPDATE rotinas SET ultima_execucao = %s WHERE id_rotina = %s", (agora, 4))


def test_rotina_ja_executada_nao_e_repetida(monkeypatch):
    agora = datetime(2026, 11, 4, 19, 0, 30)
    rotina = rotina_das_19h(ultima_execucao=datetime(2026, 11, 4, 19, 0, 10))
    cursor = usar_banco_falso(monkeypatch, servico_rotinas, todos=[[rotina]])
    assert servico_rotinas.executar_pendentes(agora) == ([], [])
    assert len(cursor.comandos) == 1  # so a listagem; nada foi executado


def test_rotina_pausada_depois_de_montar_a_fila_nao_executa(monkeypatch):
    agora = datetime(2026, 11, 4, 19, 0, 10)
    cursor = usar_banco_falso(monkeypatch, servico_rotinas,
                              todos=[[rotina_das_19h()]], um=[rotina_das_19h(ativa=False)])
    assert servico_rotinas.executar_pendentes(agora) == ([], [])
    assert not cursor.sql("UPDATE")


def test_falha_em_uma_rotina_nao_perde_as_seguintes(monkeypatch):
    agora = datetime(2026, 11, 4, 19, 0, 10)
    quebrada = rotina_das_19h(id_rotina=1, nome="Quebrada", acao="ajustar_brilho", valor=500)
    boa = rotina_das_19h(id_rotina=2, nome="Boa")
    usar_banco_falso(monkeypatch, servico_rotinas, todos=[[quebrada, boa]],
                     um=[quebrada, dict(LUZ), boa, dict(LUZ)])
    executadas, falhas = servico_rotinas.executar_pendentes(agora)
    assert executadas == ["Boa"]
    assert len(falhas) == 1 and falhas[0].startswith("Quebrada")


def test_atraso_maior_que_o_limite_nao_e_recuperado(monkeypatch):
    agora = datetime(2026, 11, 4, 19, 30)
    cursor = usar_banco_falso(monkeypatch, servico_rotinas, todos=[[rotina_das_19h()]])
    # Executor ficou parado desde 18:00: so recupera os ultimos 10 minutos.
    assert servico_rotinas.executar_pendentes(agora, desde=datetime(2026, 11, 4, 18, 0)) == ([], [])
    assert len(cursor.comandos) == 1


def test_executor_usa_o_contexto_da_aplicacao(monkeypatch):
    usar_banco_falso(monkeypatch, servico_rotinas, todos=[[]])
    with criar_app({"TESTING": True}).app_context():
        assert servico_rotinas.executar_pendentes() == ([], [])
