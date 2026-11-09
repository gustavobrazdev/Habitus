"""Estruturas de dados usadas pelo agendador: heapq (prioridade) e deque (FIFO)."""

from collections import deque
from datetime import datetime, timedelta

from app.models.rotina import dias_do_texto, proximo_horario
from app.services.rotinas import rotina_pendente
from app.structures.fila_rotinas import FilaRotinas


def criar_rotina(identificador, horario, dias="todos", ultima=None, ativa=True):
    return {
        "id_rotina": identificador,
        "horario": horario,
        "dias_semana": dias,
        "ativa": ativa,
        "ultima_execucao": ultima,
    }


def ids(comandos):
    return [rotina["id_rotina"] for rotina, _ in comandos]


def test_heap_deixa_a_rotina_mais_proxima_no_topo():
    desde = datetime(2026, 11, 4, 18, 30)
    rotinas = [
        criar_rotina(1, timedelta(hours=22)),
        criar_rotina(2, timedelta(hours=19)),
        criar_rotina(3, timedelta(hours=7)),  # ja passou hoje: proxima e amanha
    ]
    fila = FilaRotinas(rotinas, desde)
    assert len(fila) == 3
    assert fila.proxima() == datetime(2026, 11, 4, 19, 0)


def test_fila_executa_apenas_rotinas_que_chegaram_na_hora_em_ordem():
    desde = datetime(2026, 11, 4, 18, 59, 55)
    agora = datetime(2026, 11, 4, 19, 0, 15)
    rotinas = [
        criar_rotina(4, timedelta(hours=22)),
        criar_rotina(3, timedelta(hours=19)),
        criar_rotina(1, timedelta(hours=18)),
        criar_rotina(2, timedelta(hours=19)),
    ]
    fila = FilaRotinas(rotinas, desde)
    comandos = fila.comandos_ate(agora, rotina_pendente)
    assert isinstance(comandos, deque)
    # Mesmo horario: desempata pelo id. A das 22h continua esperando no heap.
    assert ids(comandos) == [2, 3]
    assert fila.proxima() == datetime(2026, 11, 4, 22, 0)


def test_fila_fifo_entrega_na_ordem_dos_horarios():
    desde = datetime(2026, 11, 4, 18, 0)
    agora = datetime(2026, 11, 4, 18, 9)
    rotinas = [criar_rotina(1, "18:05:00"), criar_rotina(2, "18:01:00"), criar_rotina(3, "18:08:00")]
    comandos = FilaRotinas(rotinas, desde).comandos_ate(agora, rotina_pendente)
    assert [comandos.popleft()[0]["id_rotina"] for _ in range(3)] == [2, 1, 3]


def test_fila_respeita_os_dias_e_a_ultima_execucao():
    desde = datetime(2026, 11, 4, 18, 59)  # quarta-feira
    agora = datetime(2026, 11, 4, 19, 0)
    rotinas = [
        criar_rotina(1, "19:00:00", dias="0,2,4"),
        criar_rotina(2, "19:00:00", dias="1,3"),
        criar_rotina(3, "19:00:00", ultima=agora),
        criar_rotina(4, "19:00:00", ativa=False),
    ]
    assert ids(FilaRotinas(rotinas, desde).comandos_ate(agora, rotina_pendente)) == [1]


def test_fila_nao_antecipa_execucao():
    agora = datetime(2026, 11, 4, 18, 59)
    rotinas = [criar_rotina(5, "19:00:00")]
    assert not FilaRotinas(rotinas, agora - timedelta(minutes=1)).comandos_ate(agora, rotina_pendente)


def test_verificacao_atrasada_nao_perde_comandos():
    # A verificacao anterior foi as 18:58 e a atual so as 19:03:
    # as rotinas das 19:00 e 19:02 ainda precisam rodar.
    desde = datetime(2026, 11, 4, 18, 58)
    agora = datetime(2026, 11, 4, 19, 3)
    rotinas = [criar_rotina(1, "19:00:00"), criar_rotina(2, "19:02:00"), criar_rotina(3, "19:05:00")]
    assert ids(FilaRotinas(rotinas, desde).comandos_ate(agora, rotina_pendente)) == [1, 2]


def test_rotina_da_meia_noite_nao_se_perde():
    desde = datetime(2026, 11, 4, 23, 59, 50)
    agora = datetime(2026, 11, 5, 0, 0, 10)  # ja e quinta-feira
    rotinas = [criar_rotina(1, "00:00:00", dias="3")]
    comandos = FilaRotinas(rotinas, desde).comandos_ate(agora, rotina_pendente)
    assert comandos[0][1] == datetime(2026, 11, 5, 0, 0)


def test_execucao_anterior_ao_horario_nao_impede_a_de_hoje():
    ontem = datetime(2026, 11, 3, 19, 0, 5)
    desde = datetime(2026, 11, 4, 18, 59, 50)
    agora = datetime(2026, 11, 4, 19, 0, 10)
    rotinas = [criar_rotina(1, "19:00:00", ultima=ontem)]
    assert ids(FilaRotinas(rotinas, desde).comandos_ate(agora, rotina_pendente)) == [1]


def test_rotina_antes_das_dez_horas_tambem_executa():
    # O MySQL devolve TIME como timedelta; str(timedelta(hours=8)) e "8:00:00".
    desde = datetime(2026, 11, 4, 7, 59, 30)
    agora = datetime(2026, 11, 4, 8, 0, 30)
    rotinas = [criar_rotina(7, timedelta(hours=8)), criar_rotina(8, timedelta(hours=7, minutes=5))]
    assert ids(FilaRotinas(rotinas, desde).comandos_ate(agora, rotina_pendente)) == [7]


def test_proximo_horario_e_conjunto_de_dias():
    base = datetime(2026, 11, 4, 18, 30)
    assert proximo_horario("19:00", base) == datetime(2026, 11, 4, 19, 0)
    assert proximo_horario("18:30", base) == datetime(2026, 11, 5, 18, 30)
    assert dias_do_texto("0,2,4") == {"0", "2", "4"}
    assert len(dias_do_texto("todos")) == 7
