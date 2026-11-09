"""Tabela usuarios."""


def inserir(cursor, nome, email, senha_hash, trocar_senha=False):
    if trocar_senha:
        cursor.execute(
            """INSERT INTO usuarios (nome, email, senha_hash, trocar_senha)
               VALUES (%s, %s, %s, 1)""",
            (nome, email, senha_hash),
        )
    else:
        # Sem a coluna trocar_senha: funciona tambem antes da migracao.
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)",
            (nome, email, senha_hash),
        )
    return cursor.lastrowid


def buscar_por_email(cursor, email, bloquear=False):
    sql = "SELECT * FROM usuarios WHERE email = %s"
    cursor.execute(sql + (" FOR UPDATE" if bloquear else ""), (email,))
    return cursor.fetchone()


def buscar_por_id(cursor, id_usuario):
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    return cursor.fetchone()


def atualizar_senha(cursor, id_usuario, senha_hash):
    cursor.execute(
        "UPDATE usuarios SET senha_hash = %s, trocar_senha = 0 WHERE id_usuario = %s",
        (senha_hash, id_usuario),
    )
