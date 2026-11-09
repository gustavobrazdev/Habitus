"""Validacoes do cadastro de dispositivos."""

from app.models.dispositivo import CLASSES
from app.validators.campos import identificador, opcao, texto


def validar_dispositivo(nome, tipo, id_comodo):
    return {
        "nome": texto(nome, "O nome do dispositivo", 2, 100),
        "tipo": opcao(tipo, CLASSES, "Escolha um tipo de dispositivo valido."),
        "id_comodo": identificador(id_comodo, "Escolha um comodo da sua casa."),
    }
