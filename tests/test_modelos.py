import pytest

from app.models.dispositivo import (
    Aquecedor, ArCondicionado, Climatizador, Generico, Luz, Ventilador,
    configuracao_inicial, criar_dispositivo,
)
from app.models.usuario import Usuario
from app.services.rotinas import dia_permitido, rotina_pendente
from datetime import datetime, timedelta


def test_luz_permite_ajustar_brilho():
    luz = criar_dispositivo({"tipo": "luz", "ligado": False, "brilho": 80})
    assert isinstance(luz, Luz)
    assert luz.executar("ajustar_brilho", "35") == ("brilho", 80, 35)


def test_valida_brilho_e_tipo():
    luz = criar_dispositivo({"tipo": "luz", "ligado": False, "brilho": 80})
    with pytest.raises(ValueError):
        luz.executar("ajustar_brilho", "letras")
    with pytest.raises(ValueError):
        luz.executar("ajustar_brilho", "101")
    with pytest.raises(ValueError):
        luz.executar("ajustar_temperatura", "25")


def test_climatizacao_tem_limites():
    ar = criar_dispositivo({"tipo": "ar_condicionado", "ligado": True, "temperatura": 23})
    assert isinstance(ar, Climatizador)
    assert ar.executar("ajustar_temperatura", "22.5") == ("temperatura", 23, 22.5)
    with pytest.raises(ValueError):
        ar.executar("ajustar_temperatura", "35")


def test_ventilador_e_dispositivo_generico():
    fan = criar_dispositivo({"tipo": "ventilador", "ligado": 0, "intensidade": 50})
    tomada = criar_dispositivo({"tipo": "outro", "ligado": 0})
    assert isinstance(fan, Ventilador)
    assert isinstance(tomada, Generico)
    assert fan.executar("ajustar_intensidade", "60") == ("intensidade", 50, 60)
    assert tomada.executar("ligar") == ("ligado", 0, 1)
    with pytest.raises(ValueError):
        tomada.executar("ajustar_brilho", "30")


def test_permissoes():
    admin = Usuario(1, "Ana", "administrador")
    comum = Usuario(2, "Carlos", "comum")
    assert admin.pode_gerenciar()
    assert not comum.pode_gerenciar()
    assert comum.pode_controlar_dispositivo()


def test_rotina_dias_da_semana():
    segunda = datetime(2026, 11, 2, 19, 0)
    assert dia_permitido("0,2,4", segunda)
    assert not dia_permitido("1,3", segunda)
    assert dia_permitido("todos", segunda)


def test_rotina_nao_repete_no_mesmo_horario():
    agendado = datetime(2026, 11, 2, 19, 0)
    rotina = {
        "horario": timedelta(hours=19), "dias_semana": "todos",
        "ativa": True, "ultima_execucao": None,
    }
    assert rotina_pendente(rotina, agendado)
    rotina["ultima_execucao"] = datetime(2026, 11, 2, 19, 0, 45)
    assert not rotina_pendente(rotina, agendado)


def test_encapsulamento_mantem_o_valor_valido():
    luz = criar_dispositivo({"tipo": "luz", "ligado": False, "brilho": 80})
    assert not luz.ligado
    assert luz.executar("ligar") == ("ligado", 0, 1)
    assert luz.ligado
    assert luz.ajustar_brilho(40) == ("brilho", 80, 40)
    assert luz.brilho == 40
    with pytest.raises(ValueError):
        luz.ajustar_brilho("101")
    assert luz.brilho == 40  # uma entrada errada nao altera o estado


def test_subclasses_do_climatizador_tem_configuracao_diferente():
    ar = criar_dispositivo({"tipo": "ar_condicionado", "ligado": False, "temperatura": 22})
    aquecedor = criar_dispositivo({"tipo": "aquecedor", "ligado": False, "temperatura": 25})
    assert isinstance(ar, ArCondicionado)
    assert isinstance(aquecedor, Aquecedor)
    assert isinstance(ar, Climatizador)
    assert isinstance(aquecedor, Climatizador)
    assert configuracao_inicial("ar_condicionado")["temperatura"] == 22
    assert configuracao_inicial("aquecedor")["temperatura"] == 25
    assert ar.executar("ajustar_temperatura", "21.5") == ("temperatura", 22, 21.5)
    assert aquecedor.executar("ajustar_temperatura", "26") == ("temperatura", 25, 26.0)


def test_temperatura_invalida_nao_muda_o_objeto():
    ar = criar_dispositivo({"tipo": "ar_condicionado", "temperatura": 22})
    for valor in ("31", "nan", "22.55", "abc"):
        with pytest.raises(ValueError):
            ar.ajustar_temperatura(valor)
    assert ar.temperatura == 22


# ---------------------------------------------------------------- POO

def test_cada_classe_sabe_sua_configuracao_inicial():
    # Polimorfismo no metodo de classe: o mesmo metodo, resultados diferentes.
    assert Luz.configuracao_inicial() == {"brilho": 80, "temperatura": None, "intensidade": None}
    assert Ventilador.configuracao_inicial()["intensidade"] == 50
    assert Generico.configuracao_inicial() == {"brilho": None, "temperatura": None, "intensidade": None}
    with pytest.raises(ValueError):
        configuracao_inicial("geladeira")


def test_acoes_permitidas_sao_herdadas_e_ampliadas():
    assert Generico.acoes_permitidas == {"ligar", "desligar"}
    assert Luz.acoes_permitidas == {"ligar", "desligar", "ajustar_brilho"}
    assert ArCondicionado.acoes_permitidas == Climatizador.acoes_permitidas
    assert "ajustar_brilho" not in Aquecedor.acoes_permitidas


def test_polimorfismo_mesma_chamada_para_classes_diferentes():
    dispositivos = [
        criar_dispositivo({"tipo": "luz", "brilho": 80}),
        criar_dispositivo({"tipo": "ventilador", "intensidade": 50}),
        criar_dispositivo({"tipo": "aquecedor", "temperatura": 25}),
    ]
    acoes = ["ajustar_brilho", "ajustar_intensidade", "ajustar_temperatura"]
    resultados = [d.executar(acao, "20") for d, acao in zip(dispositivos, acoes)]
    assert resultados == [("brilho", 80, 20), ("intensidade", 50, 20), ("temperatura", 25, 20.0)]


def test_limites_vem_do_atributo_da_classe():
    from app.models.dispositivo import AJUSTES
    assert AJUSTES["ajustar_temperatura"]["minimo"] == 16
    assert AJUSTES["ajustar_temperatura"]["maximo"] == 30
    assert set(AJUSTES) == {"ajustar_brilho", "ajustar_temperatura", "ajustar_intensidade"}
