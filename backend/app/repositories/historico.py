"""Tabela historico: registro do que mudou nos dispositivos."""


def registrar(cursor, id_dispositivo, id_usuario, acao, anterior, novo):
    cursor.execute(
        """INSERT INTO historico
           (id_dispositivo, id_usuario, acao, valor_anterior, valor_novo)
           VALUES (%s, %s, %s, %s, %s)""",
        (
            id_dispositivo, id_usuario, acao[:60],
            str(anterior)[:50] if anterior is not None else None,
            str(novo)[:50] if novo is not None else None,
        ),
    )


def listar_da_casa(cursor, id_casa, limite=100):
    cursor.execute(
        """SELECT h.*, d.nome AS dispositivo, c.nome AS comodo, u.nome AS usuario
           FROM historico h
           JOIN dispositivos d ON d.id_dispositivo = h.id_dispositivo
           JOIN comodos c ON c.id_comodo = d.id_comodo
           LEFT JOIN usuarios u ON u.id_usuario = h.id_usuario
           WHERE c.id_casa = %s ORDER BY h.data_acao DESC, h.id_historico DESC
           LIMIT %s""",
        (id_casa, limite),
    )
    return cursor.fetchall()
