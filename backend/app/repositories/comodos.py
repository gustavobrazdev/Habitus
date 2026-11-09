"""Tabela comodos."""


def listar(cursor, id_casa):
    cursor.execute(
        "SELECT id_comodo, nome FROM comodos WHERE id_casa = %s ORDER BY nome", (id_casa,)
    )
    return cursor.fetchall()


def listar_com_dispositivos(cursor, id_casa):
    """Comodos com a quantidade de dispositivos (ativos e removidos)."""
    cursor.execute(
        """SELECT c.id_comodo, c.nome,
                  COUNT(d.id_dispositivo) AS total_dispositivos,
                  COALESCE(SUM(d.ativo = 1), 0) AS dispositivos_ativos
           FROM comodos c
           LEFT JOIN dispositivos d ON d.id_comodo = c.id_comodo
           WHERE c.id_casa = %s
           GROUP BY c.id_comodo, c.nome
           ORDER BY c.nome""",
        (id_casa,),
    )
    return cursor.fetchall()


def buscar(cursor, id_casa, id_comodo, bloquear=False):
    sql = "SELECT * FROM comodos WHERE id_comodo = %s AND id_casa = %s"
    cursor.execute(sql + (" FOR UPDATE" if bloquear else ""), (id_comodo, id_casa))
    return cursor.fetchone()


def inserir(cursor, id_casa, nome):
    cursor.execute("INSERT INTO comodos (id_casa, nome) VALUES (%s, %s)", (id_casa, nome))
    return cursor.lastrowid


def renomear(cursor, id_casa, id_comodo, nome):
    cursor.execute(
        "UPDATE comodos SET nome = %s WHERE id_comodo = %s AND id_casa = %s",
        (nome, id_comodo, id_casa),
    )


def contar_dispositivos(cursor, id_comodo):
    cursor.execute(
        """SELECT COUNT(*) AS total, COALESCE(SUM(ativo = 1), 0) AS ativos
           FROM dispositivos WHERE id_comodo = %s""",
        (id_comodo,),
    )
    return cursor.fetchone()


def excluir(cursor, id_casa, id_comodo):
    cursor.execute(
        "DELETE FROM comodos WHERE id_comodo = %s AND id_casa = %s", (id_comodo, id_casa)
    )
