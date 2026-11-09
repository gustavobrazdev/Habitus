"""Tabela dispositivos.

Dispositivos nao sao apagados: "remover" marca ativo = 0 para manter o historico.
"""

# Colunas que os controles podem alterar. O nome da coluna vem das classes,
# nunca do formulario, e mesmo assim e conferido aqui.
CAMPOS_CONTROLE = {"ligado", "brilho", "temperatura", "intensidade"}


def listar_ativos_da_casa(cursor, id_casa):
    cursor.execute(
        """SELECT d.*, c.nome AS nome_comodo FROM dispositivos d
           JOIN comodos c ON c.id_comodo = d.id_comodo
           WHERE c.id_casa = %s AND d.ativo = 1
           ORDER BY c.nome, d.nome""",
        (id_casa,),
    )
    return cursor.fetchall()


def buscar_ativo(cursor, id_dispositivo, id_casa=None, bloquear=False):
    """Busca um dispositivo ativo. Com id_casa, so encontra se for daquela casa."""
    sql = """SELECT d.*, c.id_casa, c.nome AS nome_comodo FROM dispositivos d
             JOIN comodos c ON c.id_comodo = d.id_comodo
             WHERE d.id_dispositivo = %s AND d.ativo = 1"""
    parametros = [id_dispositivo]
    if id_casa is not None:
        sql += " AND c.id_casa = %s"
        parametros.append(id_casa)
    cursor.execute(sql + (" FOR UPDATE" if bloquear else ""), parametros)
    return cursor.fetchone()


def inserir(cursor, id_comodo, nome, tipo, configuracao):
    cursor.execute(
        """INSERT INTO dispositivos (id_comodo, nome, tipo, brilho, temperatura, intensidade)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (id_comodo, nome, tipo, configuracao["brilho"],
         configuracao["temperatura"], configuracao["intensidade"]),
    )
    return cursor.lastrowid


def atualizar_campo(cursor, id_dispositivo, campo, valor):
    if campo not in CAMPOS_CONTROLE:
        raise ValueError("Campo de controle invalido.")
    cursor.execute(
        f"UPDATE dispositivos SET {campo} = %s WHERE id_dispositivo = %s",
        (valor, id_dispositivo),
    )


def mudar_comodo(cursor, id_dispositivo, id_comodo):
    cursor.execute(
        "UPDATE dispositivos SET id_comodo = %s WHERE id_dispositivo = %s",
        (id_comodo, id_dispositivo),
    )


def desativar(cursor, id_dispositivo, id_casa):
    """Devolve True se o dispositivo era da casa e foi removido da lista."""
    cursor.execute(
        """UPDATE dispositivos d JOIN comodos c ON c.id_comodo = d.id_comodo
           SET d.ativo = 0
           WHERE d.id_dispositivo = %s AND c.id_casa = %s AND d.ativo = 1""",
        (id_dispositivo, id_casa),
    )
    return cursor.rowcount > 0
