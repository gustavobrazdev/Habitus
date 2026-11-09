"""Tabela casas."""


def inserir(cursor, nome):
    cursor.execute("INSERT INTO casas (nome) VALUES (%s)", (nome,))
    return cursor.lastrowid


def listar_do_usuario(cursor, id_usuario):
    cursor.execute(
        """SELECT c.id_casa, c.nome, m.perfil FROM casas c
           JOIN moradores m ON m.id_casa = c.id_casa
           WHERE m.id_usuario = %s ORDER BY c.nome""",
        (id_usuario,),
    )
    return cursor.fetchall()
