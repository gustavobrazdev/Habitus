"""Validacoes centralizadas em app/validators."""

import pytest

from app.validators.campos import identificador, numero_decimal, numero_inteiro, texto
from app.validators.casas import validar_nome_comodo, validar_opcao_comodos
from app.validators.dispositivos import validar_dispositivo
from app.validators.rotinas import validar_dias, validar_horario, validar_rotina
from app.validators.usuarios import validar_email, validar_perfil, validar_senha


def test_texto_remove_espacos_e_confere_tamanho():
    assert texto("  Sala   de  TV ", "O nome", 2, 80) == "Sala de TV"
    with pytest.raises(ValueError, match="O nome deve ter de 2 a 80"):
        texto(" a ", "O nome", 2, 80)
    with pytest.raises(ValueError):
        texto(None, "O nome", 2, 80)


@pytest.mark.parametrize("valor", ["", "abc", "0", "-3", "2.5", None])
def test_identificador_invalido(valor):
    with pytest.raises(ValueError, match="Escolha"):
        identificador(valor, "Escolha um comodo.")


def test_identificador_valido():
    assert identificador(" 12 ", "Escolha") == 12


def test_numeros():
    assert numero_inteiro("40", 0, 100, "O brilho") == 40
    assert numero_inteiro("40,0", 0, 100, "O brilho") == 40
    assert numero_decimal("22,5", 16, 30, "A temperatura") == 22.5
    for valor in ("letras", "nan", "inf", "40.5", "101"):
        with pytest.raises(ValueError):
            numero_inteiro(valor, 0, 100, "O brilho")
    for valor in ("15.9", "22.55", ""):
        with pytest.raises(ValueError):
            numero_decimal(valor, 16, 30, "A temperatura")


def test_usuario():
    assert validar_email("  Ana@Exemplo.COM ") == "ana@exemplo.com"
    for email in ("ana", "ana@", "ana @x.com", "a@b", "x" * 150 + "@a.com"):
        with pytest.raises(ValueError, match="e-mail"):
            validar_email(email)
    assert validar_senha("12345678", "12345678") == "12345678"
    with pytest.raises(ValueError, match="8 caracteres"):
        validar_senha("1234567", "1234567")
    with pytest.raises(ValueError, match="nao conferem"):
        validar_senha("12345678", "87654321")
    assert validar_perfil("comum") == "comum"
    with pytest.raises(ValueError):
        validar_perfil("dono")


def test_casa_e_comodo():
    assert validar_nome_comodo(" Home  office ") == "Home office"
    with pytest.raises(ValueError):
        validar_nome_comodo("x" * 81)
    assert validar_opcao_comodos("vazio") == "vazio"
    with pytest.raises(ValueError):
        validar_opcao_comodos("outra")


def test_dispositivo():
    assert validar_dispositivo(" Luz ", "luz", "3") == {"nome": "Luz", "tipo": "luz", "id_comodo": 3}
    with pytest.raises(ValueError, match="tipo"):
        validar_dispositivo("Luz", "torradeira", "3")


def test_horario_e_dias():
    assert validar_horario("07:05") == "07:05"
    for horario in ("25:00", "7h", "", None):
        with pytest.raises(ValueError, match="horario"):
            validar_horario(horario)
    assert validar_dias(["0", "2", "2"]) == {"0", "2"}  # o conjunto descarta repetidos
    for dias in ([], ["7"], ["seg"]):
        with pytest.raises(ValueError, match="dia"):
            validar_dias(dias)


def test_rotina_completa():
    dados = validar_rotina({"nome": " Noite ", "id_dispositivo": "5", "acao": "ajustar_brilho",
                            "valor": "70", "horario": "22:00", "dias": ["4", "0"]})
    assert dados == {"nome": "Noite", "id_dispositivo": 5, "acao": "ajustar_brilho",
                     "valor": "70", "horario": "22:00", "dias_semana": "0,4"}
    ligar = validar_rotina({"nome": "Manha", "id_dispositivo": "5", "acao": "ligar",
                            "valor": "70", "horario": "07:00", "dias": list("0123456")})
    assert ligar["valor"] is None and ligar["dias_semana"] == "todos"
    with pytest.raises(ValueError, match="valor do ajuste"):
        validar_rotina({"nome": "X1", "id_dispositivo": "5", "acao": "ajustar_brilho",
                        "valor": "", "horario": "07:00", "dias": ["0"]})
    with pytest.raises(ValueError, match="acao"):
        validar_rotina({"nome": "X1", "id_dispositivo": "5", "acao": "explodir",
                        "horario": "07:00", "dias": ["0"]})
