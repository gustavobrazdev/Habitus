"""Validacoes genericas: textos obrigatorios, identificadores e numeros."""

from decimal import Decimal, InvalidOperation


def texto(valor, campo, minimo, maximo):
    """Tira espacos repetidos e confere o tamanho. Ex.: '  Sala   de TV ' -> 'Sala de TV'."""
    limpo = " ".join(str(valor or "").split())
    if not minimo <= len(limpo) <= maximo:
        raise ValueError(f"{campo} deve ter de {minimo} a {maximo} caracteres.")
    return limpo


def identificador(valor, mensagem):
    """Numero inteiro positivo vindo de um <select>, como id_comodo."""
    limpo = str(valor or "").strip()
    if not limpo.isdigit() or int(limpo) == 0:
        raise ValueError(mensagem)
    return int(limpo)


def opcao(valor, opcoes_validas, mensagem):
    if valor not in opcoes_validas:
        raise ValueError(mensagem)
    return valor


def _converter(valor, nome, mensagem):
    try:
        numero = Decimal(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError, InvalidOperation):
        raise ValueError(f"{nome} {mensagem}.")
    if not numero.is_finite():
        raise ValueError(f"{nome} {mensagem}.")
    return numero


def numero_inteiro(valor, minimo, maximo, nome):
    numero = _converter(valor, nome, "precisa ser um numero inteiro")
    if numero != numero.to_integral_value():
        raise ValueError(f"{nome} precisa ser um numero inteiro.")
    if not minimo <= numero <= maximo:
        raise ValueError(f"{nome} deve ficar entre {minimo} e {maximo}.")
    return int(numero)


def numero_decimal(valor, minimo, maximo, nome):
    """Aceita uma casa decimal, como 22.5 ou 22,5."""
    numero = _converter(valor, nome, "precisa ser um numero")
    if not Decimal(str(minimo)) <= numero <= Decimal(str(maximo)):
        raise ValueError(f"{nome} deve ficar entre {minimo} e {maximo}.")
    if numero != numero.quantize(Decimal("0.1")):
        raise ValueError(f"{nome} aceita uma casa decimal.")
    return float(numero)
