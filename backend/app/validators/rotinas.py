"""Validacoes do formulario de rotinas (nome, acao, horario e dias)."""

from datetime import datetime

from app.models.rotina import ACOES, TODOS_OS_DIAS, dias_para_texto
from app.validators.campos import identificador, opcao, texto


def validar_horario(horario):
    try:
        return datetime.strptime(str(horario), "%H:%M").strftime("%H:%M")
    except ValueError:
        raise ValueError("Informe um horario valido, no formato HH:MM.")


def validar_dias(dias):
    """Recebe a lista dos checkboxes e devolve o conjunto de dias escolhidos."""
    dias = set(dias)
    if not dias or not dias <= TODOS_OS_DIAS:
        raise ValueError("Selecione pelo menos um dia da semana.")
    return dias


def validar_rotina(formulario):
    """Confere os campos que nao dependem do dispositivo.

    O valor do ajuste (brilho, temperatura...) e validado depois pela classe
    do dispositivo escolhido, porque cada uma tem seus limites.
    """
    acao = opcao(formulario.get("acao"), ACOES, "Escolha uma acao valida.")
    valor = str(formulario.get("valor") or "").strip()
    if acao.startswith("ajustar_") and not valor:
        raise ValueError("Escolha o valor do ajuste.")
    return {
        "nome": texto(formulario.get("nome"), "O nome da rotina", 2, 100),
        "id_dispositivo": identificador(formulario.get("id_dispositivo"), "Escolha um dispositivo."),
        "acao": acao,
        "valor": valor if acao.startswith("ajustar_") else None,
        "horario": validar_horario(formulario.get("horario")),
        "dias_semana": dias_para_texto(validar_dias(formulario.get("dias", ()))),
    }
