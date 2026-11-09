"""Tabela moradores: liga usuarios as casas com um perfil de acesso."""

CONSULTA_ACESSO = """SELECT u.id_usuario, u.nome, m.perfil, c.id_casa, c.nome AS nome_casa
                     FROM moradores m
                     JOIN usuarios u ON u.id_usuario = m.id_usuario
                     JOIN casas c ON c.id_casa = m.id_casa"""


def buscar_acesso(cursor, id_usuario, id_casa):
    cursor.execute(
        CONSULTA_ACESSO + " WHERE m.id_usuario = %s AND m.id_casa = %s",
        (id_usuario, id_casa),
    )
    return cursor.fetchone()


def buscar_primeiro_acesso(cursor, id_usuario):
    cursor.execute(
        CONSULTA_ACESSO + " WHERE m.id_usuario = %s ORDER BY m.id_morador LIMIT 1",
        (id_usuario,),
    )
    return cursor.fetchone()


def listar_da_casa(cursor, id_casa):
    cursor.execute(
        """SELECT m.id_morador, m.id_usuario, m.perfil, u.nome, u.email
           FROM moradores m JOIN usuarios u ON u.id_usuario = m.id_usuario
           WHERE m.id_casa = %s ORDER BY m.perfil, u.nome""",
        (id_casa,),
    )
    return cursor.fetchall()


def participa(cursor, id_usuario, id_casa):
    cursor.execute(
        "SELECT 1 FROM moradores WHERE id_usuario = %s AND id_casa = %s",
        (id_usuario, id_casa),
    )
    return cursor.fetchone() is not None


def inserir(cursor, id_casa, id_usuario, perfil):
    cursor.execute(
        "INSERT INTO moradores (id_casa, id_usuario, perfil) VALUES (%s, %s, %s)",
        (id_casa, id_usuario, perfil),
    )


def buscar(cursor, id_morador, id_casa, bloquear=False):
    sql = "SELECT * FROM moradores WHERE id_morador = %s AND id_casa = %s"
    cursor.execute(sql + (" FOR UPDATE" if bloquear else ""), (id_morador, id_casa))
    return cursor.fetchone()


def atualizar_perfil(cursor, id_morador, perfil):
    cursor.execute(
        "UPDATE moradores SET perfil = %s WHERE id_morador = %s", (perfil, id_morador)
    )


def excluir(cursor, id_morador):
    cursor.execute("DELETE FROM moradores WHERE id_morador = %s", (id_morador,))
