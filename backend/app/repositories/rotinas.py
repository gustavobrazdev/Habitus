"""Tabela rotinas."""

CONSULTA_DA_CASA = """SELECT r.*, d.nome AS nome_dispositivo, d.tipo, c.nome AS nome_comodo
                      FROM rotinas r
                      JOIN dispositivos d ON d.id_dispositivo = r.id_dispositivo
                      JOIN comodos c ON c.id_comodo = d.id_comodo
                      WHERE c.id_casa = %s AND d.ativo = 1"""


def listar_da_casa(cursor, id_casa):
    cursor.execute(CONSULTA_DA_CASA + " ORDER BY r.horario, r.nome", (id_casa,))
    return cursor.fetchall()


def buscar_da_casa(cursor, id_rotina, id_casa, bloquear=False):
    sql = CONSULTA_DA_CASA + " AND r.id_rotina = %s"
    cursor.execute(sql + (" FOR UPDATE" if bloquear else ""), (id_casa, id_rotina))
    return cursor.fetchone()


def contar_ativas(cursor, id_casa):
    cursor.execute(
        """SELECT COUNT(*) AS total FROM rotinas r
           JOIN dispositivos d ON d.id_dispositivo = r.id_dispositivo
           JOIN comodos c ON c.id_comodo = d.id_comodo
           WHERE c.id_casa = %s AND r.ativa = 1 AND d.ativo = 1""",
        (id_casa,),
    )
    return cursor.fetchone()["total"]


def listar_ativas(cursor):
    """Usada pelo executor: rotinas ativas de todas as casas."""
    cursor.execute(
        """SELECT r.* FROM rotinas r
           JOIN dispositivos d ON d.id_dispositivo = r.id_dispositivo
           WHERE r.ativa = 1 AND d.ativo = 1"""
    )
    return cursor.fetchall()


def buscar_por_id(cursor, id_rotina, bloquear=False):
    sql = "SELECT * FROM rotinas WHERE id_rotina = %s"
    cursor.execute(sql + (" FOR UPDATE" if bloquear else ""), (id_rotina,))
    return cursor.fetchone()


def inserir(cursor, dados):
    cursor.execute(
        """INSERT INTO rotinas (id_dispositivo, nome, acao, valor, horario, dias_semana)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (dados["id_dispositivo"], dados["nome"], dados["acao"], dados["valor"],
         dados["horario"], dados["dias_semana"]),
    )
    return cursor.lastrowid


def atualizar(cursor, id_rotina, dados):
    cursor.execute(
        """UPDATE rotinas SET id_dispositivo = %s, nome = %s, acao = %s,
                  valor = %s, horario = %s, dias_semana = %s
           WHERE id_rotina = %s""",
        (dados["id_dispositivo"], dados["nome"], dados["acao"], dados["valor"],
         dados["horario"], dados["dias_semana"], id_rotina),
    )


def alternar(cursor, id_rotina):
    cursor.execute("UPDATE rotinas SET ativa = 1 - ativa WHERE id_rotina = %s", (id_rotina,))


def excluir(cursor, id_rotina):
    cursor.execute("DELETE FROM rotinas WHERE id_rotina = %s", (id_rotina,))


def pausar_do_dispositivo(cursor, id_dispositivo):
    cursor.execute("UPDATE rotinas SET ativa = 0 WHERE id_dispositivo = %s", (id_dispositivo,))


def marcar_execucao(cursor, id_rotina, quando):
    cursor.execute(
        "UPDATE rotinas SET ultima_execucao = %s WHERE id_rotina = %s", (quando, id_rotina)
    )
