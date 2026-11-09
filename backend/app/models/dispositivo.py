"""Classes dos dispositivos da casa.

Cada classe guarda o proprio estado (encapsulamento), herda o liga/desliga
de Dispositivo (heranca) e responde ao mesmo metodo executar() do seu jeito
(polimorfismo). Os limites de cada ajuste ficam no atributo `ajuste` da classe,
e o resto do sistema (formularios, rotinas e telas) le esses dados daqui.
"""

from app.validators.campos import numero_decimal, numero_inteiro


class Dispositivo:
    """Comportamento comum: todo dispositivo liga e desliga."""

    acoes_permitidas = frozenset({"ligar", "desligar"})
    ajuste = None          # dispositivos simples nao tem controle extra
    valor_inicial = None

    def __init__(self, dados):
        self._ligado = bool(dados.get("ligado", False))

    @property
    def ligado(self):
        return self._ligado

    @classmethod
    def configuracao_inicial(cls):
        """Valores das colunas brilho/temperatura/intensidade ao cadastrar."""
        configuracao = {"brilho": None, "temperatura": None, "intensidade": None}
        if cls.ajuste:
            configuracao[cls.ajuste["campo"]] = cls.valor_inicial
        return configuracao

    def ligar(self):
        anterior = int(self._ligado)
        self._ligado = True
        return "ligado", anterior, 1

    def desligar(self):
        anterior = int(self._ligado)
        self._ligado = False
        return "ligado", anterior, 0

    def executar(self, acao, valor=None):
        """Devolve (coluna alterada, valor anterior, valor novo)."""
        if acao == "ligar":
            return self.ligar()
        if acao == "desligar":
            return self.desligar()
        raise ValueError("Esse controle nao funciona neste dispositivo.")


class Luz(Dispositivo):
    ajuste = {"acao": "ajustar_brilho", "campo": "brilho", "titulo": "Brilho",
              "minimo": 0, "maximo": 100, "passo": 1, "unidade": "%"}
    acoes_permitidas = Dispositivo.acoes_permitidas | {"ajustar_brilho"}
    valor_inicial = 80

    def __init__(self, dados):
        super().__init__(dados)
        self._brilho = dados.get("brilho")

    @property
    def brilho(self):
        return self._brilho

    def ajustar_brilho(self, valor):
        novo = numero_inteiro(valor, self.ajuste["minimo"], self.ajuste["maximo"], "O brilho")
        anterior = self._brilho
        self._brilho = novo
        return "brilho", anterior, novo

    def executar(self, acao, valor=None):
        if acao == "ajustar_brilho":
            return self.ajustar_brilho(valor)
        return super().executar(acao, valor)


class Climatizador(Dispositivo):
    """Codigo que o ar-condicionado e o aquecedor compartilham."""

    ajuste = {"acao": "ajustar_temperatura", "campo": "temperatura", "titulo": "Temperatura",
              "minimo": 16, "maximo": 30, "passo": 0.5, "unidade": " °C"}
    acoes_permitidas = Dispositivo.acoes_permitidas | {"ajustar_temperatura"}
    valor_inicial = 23

    def __init__(self, dados):
        super().__init__(dados)
        self._temperatura = dados.get("temperatura")

    @property
    def temperatura(self):
        return self._temperatura

    def ajustar_temperatura(self, valor):
        novo = numero_decimal(valor, self.ajuste["minimo"], self.ajuste["maximo"], "A temperatura")
        anterior = self._temperatura
        self._temperatura = novo
        return "temperatura", anterior, novo

    def executar(self, acao, valor=None):
        if acao == "ajustar_temperatura":
            return self.ajustar_temperatura(valor)
        return super().executar(acao, valor)


class ArCondicionado(Climatizador):
    valor_inicial = 22  # comeca refrigerando


class Aquecedor(Climatizador):
    valor_inicial = 25  # comeca aquecendo


class Ventilador(Dispositivo):
    ajuste = {"acao": "ajustar_intensidade", "campo": "intensidade", "titulo": "Intensidade",
              "minimo": 0, "maximo": 100, "passo": 1, "unidade": "%"}
    acoes_permitidas = Dispositivo.acoes_permitidas | {"ajustar_intensidade"}
    valor_inicial = 50

    def __init__(self, dados):
        super().__init__(dados)
        self._intensidade = dados.get("intensidade")

    @property
    def intensidade(self):
        return self._intensidade

    def ajustar_intensidade(self, valor):
        novo = numero_inteiro(valor, self.ajuste["minimo"], self.ajuste["maximo"], "A intensidade")
        anterior = self._intensidade
        self._intensidade = novo
        return "intensidade", anterior, novo

    def executar(self, acao, valor=None):
        if acao == "ajustar_intensidade":
            return self.ajustar_intensidade(valor)
        return super().executar(acao, valor)


class Generico(Dispositivo):
    """Tomadas e outros aparelhos que so ligam e desligam."""


# Dicionario: escolhe a classe pelo tipo salvo no banco, sem varios if/elif.
CLASSES = {
    "luz": Luz,
    "ar_condicionado": ArCondicionado,
    "aquecedor": Aquecedor,
    "ventilador": Ventilador,
    "outro": Generico,
}

TIPOS = {
    "luz": "Luz",
    "ar_condicionado": "Ar-condicionado",
    "aquecedor": "Aquecedor",
    "ventilador": "Ventilador",
    "outro": "Outro dispositivo",
}

# Limites de cada acao de ajuste, usados pela tela de rotinas.
AJUSTES = {classe.ajuste["acao"]: classe.ajuste for classe in CLASSES.values() if classe.ajuste}


def classe_do_tipo(tipo):
    classe = CLASSES.get(tipo)
    if classe is None:
        raise ValueError("Tipo de dispositivo nao encontrado.")
    return classe


def criar_dispositivo(dados):
    return classe_do_tipo(dados.get("tipo"))(dados)


def configuracao_inicial(tipo):
    return classe_do_tipo(tipo).configuracao_inicial()
