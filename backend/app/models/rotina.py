"""Classe que transforma uma linha da tabela `rotinas` em texto para a tela."""

from datetime import datetime, timedelta
from decimal import Decimal

from app.models.dispositivo import AJUSTES


ACOES = {
    "ligar": "Ligar",
    "desligar": "Desligar",
    "ajustar_brilho": "Ajustar brilho",
    "ajustar_temperatura": "Ajustar temperatura",
    "ajustar_intensidade": "Ajustar intensidade",
}

# Unidade de cada ajuste, lida das classes dos dispositivos (ex.: "%" ou " °C").
UNIDADES = {acao: ajuste["unidade"] for acao, ajuste in AJUSTES.items()}

# Mesma numeracao do datetime.weekday(): 0 = segunda ... 6 = domingo.
DIAS_DA_SEMANA = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
TODOS_OS_DIAS = {str(numero) for numero in range(7)}


def formatar_horario(horario):
    """O MySQL devolve TIME como timedelta; aqui vira sempre 'HH:MM'."""
    if hasattr(horario, "total_seconds"):
        minutos = int(horario.total_seconds()) // 60
        return f"{minutos // 60:02d}:{minutos % 60:02d}"
    return datetime.strptime(str(horario)[:5], "%H:%M").strftime("%H:%M")


def proximo_horario(horario, depois_de):
    """Primeira data e hora com esse horario que vem depois de `depois_de`.

    Ex.: horario 19:00 e depois_de 18:30 -> hoje 19:00;
         horario 07:00 e depois_de 18:30 -> amanha 07:00.
    """
    hora, minuto = (int(parte) for parte in formatar_horario(horario).split(":"))
    candidato = depois_de.replace(hour=hora, minute=minuto, second=0, microsecond=0)
    if candidato <= depois_de:
        candidato += timedelta(days=1)
    return candidato


def formatar_numero(valor):
    """Decimal('75.0') -> '75' e Decimal('22.5') -> '22,5'."""
    if valor is None:
        return ""
    numero = Decimal(str(valor))
    if numero == numero.to_integral_value():
        return str(int(numero))
    return f"{numero:.1f}".replace(".", ",")


def dias_do_texto(dias_semana):
    """'todos' ou '0,2,4' -> conjunto de dias."""
    if dias_semana == "todos":
        return set(TODOS_OS_DIAS)
    return {dia.strip() for dia in str(dias_semana).split(",") if dia.strip()}


def dias_para_texto(dias):
    """Conjunto de dias -> texto salvo no banco ('todos' ou '0,2,4')."""
    return "todos" if set(dias) == TODOS_OS_DIAS else ",".join(sorted(dias))


class Rotina:
    def __init__(self, dados):
        self.id_rotina = dados.get("id_rotina")
        self.id_dispositivo = dados.get("id_dispositivo")
        self.nome = dados.get("nome")
        self.acao = dados.get("acao")
        self.valor = dados.get("valor")
        self.horario = formatar_horario(dados.get("horario"))
        self.dias = dias_do_texto(dados.get("dias_semana", "todos"))
        self.ativa = bool(dados.get("ativa"))
        self.nome_dispositivo = dados.get("nome_dispositivo")
        self.nome_comodo = dados.get("nome_comodo")

    @property
    def precisa_valor(self):
        return self.acao in UNIDADES

    @property
    def valor_texto(self):
        """Ex.: '75%' ou '23 °C'. Vazio para ligar e desligar."""
        if not self.precisa_valor or self.valor is None:
            return ""
        return formatar_numero(self.valor) + UNIDADES[self.acao]

    @property
    def acao_texto(self):
        texto = ACOES.get(self.acao, self.acao)
        return f"{texto} para {self.valor_texto}" if self.valor_texto else texto

    @property
    def dias_texto(self):
        if self.dias == TODOS_OS_DIAS:
            return "Todos os dias"
        if self.dias == {"0", "1", "2", "3", "4"}:
            return "Segunda a sexta"
        if self.dias == {"5", "6"}:
            return "Fins de semana"
        return ", ".join(DIAS_DA_SEMANA[int(dia)] for dia in sorted(self.dias))

    @property
    def valor_formulario(self):
        """Valor usado para preencher o controle deslizante na edicao."""
        return "" if self.valor is None else formatar_numero(self.valor).replace(",", ".")
