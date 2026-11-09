
import os
from pathlib import Path
import pytest

import pymysql
from dotenv import load_dotenv

# Carrega as credenciais existentes, sem alterar o .env.
RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")


def test_conexao_mysql():
    conexao = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database="habitus_testes",
        connect_timeout=5,
    )

    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            banco = cursor.fetchone()[0]

            assert banco == "habitus_testes"

            cursor.execute("SHOW TABLES")
            tabelas = {linha[0] for linha in cursor.fetchall()}

            esperadas = {
                "usuarios", "casas", "moradores",
                "comodos", "dispositivos",
                "historico", "rotinas",
            }

            assert tabelas == esperadas
    finally:
        conexao.close()


from uuid import uuid4
from werkzeug.security import generate_password_hash


def test_crud_usuarios_mysql():
    # Conecta exclusivamente ao banco de testes.
    conexao = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database="habitus_testes",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=5,
    )

    try:
        with conexao.cursor() as cursor:
            # Confirma o banco ANTES de modificar dados.
            cursor.execute("SELECT DATABASE() AS banco")
            assert cursor.fetchone()["banco"] == "habitus_testes"

            nome = "Usuario Teste"
            email = f"teste_{uuid4().hex}@example.invalid"
            senha_hash = generate_password_hash("SenhaTeste123!")

            # 1. CREATE - Cadastrar usuário
            cursor.execute(
                """
                INSERT INTO usuarios (nome, email, senha_hash)
                VALUES (%s, %s, %s)
                """,
                (nome, email, senha_hash),
            )

            id_usuario = cursor.lastrowid
            assert id_usuario is not None

            # 2. READ - Consultar usuário
            cursor.execute(
                "SELECT * FROM usuarios WHERE id_usuario = %s",
                (id_usuario,),
            )

            usuario = cursor.fetchone()

            assert usuario is not None
            assert usuario["nome"] == "Usuario Teste"
            assert usuario["email"] == email

            # 3. UPDATE - Atualizar nome
            cursor.execute(
                """
                UPDATE usuarios
                SET nome = %s
                WHERE id_usuario = %s
                """,
                ("Usuario Atualizado", id_usuario),
            )

            assert cursor.rowcount == 1

            cursor.execute(
                "SELECT nome FROM usuarios WHERE id_usuario = %s",
                (id_usuario,),
            )

            usuario = cursor.fetchone()
            assert usuario["nome"] == "Usuario Atualizado"

            # 4. DELETE - Excluir usuário
            cursor.execute(
                "DELETE FROM usuarios WHERE id_usuario = %s",
                (id_usuario,),
            )

            assert cursor.rowcount == 1

            cursor.execute(
                "SELECT * FROM usuarios WHERE id_usuario = %s",
                (id_usuario,),
            )

            assert cursor.fetchone() is None

    finally:
        # Desfaz as alterações, mesmo se o teste falhar.
        conexao.rollback()
        conexao.close()



def test_relacionamentos_mysql():
    import pytest
    from uuid import uuid4
    from werkzeug.security import generate_password_hash

    conexao = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database="habitus_testes",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=5,
    )

    try:
        with conexao.cursor() as cursor:
            # Verifica o banco e as chaves estrangeiras
            cursor.execute(
                "SELECT DATABASE() AS banco, "
                "@@FOREIGN_KEY_CHECKS AS fk_ativas"
            )
            config = cursor.fetchone()

            assert config["banco"] == "habitus_testes"
            assert config["fk_ativas"] == 1

            # 1. CREATE - Criar dois usuarios
            usuarios = []

            for nome in ("Admin Teste", "Morador Teste"):
                email = f"teste_{uuid4().hex}@example.invalid"

                cursor.execute(
                    """
                    INSERT INTO usuarios
                        (nome, email, senha_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        nome,
                        email,
                        generate_password_hash("SenhaTeste123!"),
                    ),
                )
                usuarios.append(cursor.lastrowid)

            id_admin, id_comum = usuarios

            # 2. CREATE - Criar duas casas
            cursor.execute(
                "INSERT INTO casas (nome) VALUES (%s)",
                ("Casa Teste A",),
            )
            id_casa_a = cursor.lastrowid

            cursor.execute(
                "INSERT INTO casas (nome) VALUES (%s)",
                ("Casa Teste B",),
            )
            id_casa_b = cursor.lastrowid

            # 3. Vincular usuarios e casas
            vinculos = [
                (id_casa_a, id_admin, "administrador"),
                (id_casa_a, id_comum, "comum"),
                (id_casa_b, id_admin, "comum"),
            ]

            for casa, usuario, perfil in vinculos:
                cursor.execute(
                    """
                    INSERT INTO moradores
                        (id_casa, id_usuario, perfil)
                    VALUES (%s, %s, %s)
                    """,
                    (casa, usuario, perfil),
                )

            # 4. READ - Conferir os relacionamentos
            cursor.execute(
                """
                SELECT m.perfil
                FROM moradores m
                JOIN usuarios u
                  ON u.id_usuario = m.id_usuario
                JOIN casas c
                  ON c.id_casa = m.id_casa
                WHERE m.id_usuario = %s
                  AND m.id_casa = %s
                """,
                (id_admin, id_casa_a),
            )
            assert cursor.fetchone()["perfil"] == "administrador"

            cursor.execute(
                """
                SELECT perfil FROM moradores
                WHERE id_usuario = %s AND id_casa = %s
                """,
                (id_admin, id_casa_b),
            )
            assert cursor.fetchone()["perfil"] == "comum"

            # 5. Impedir usuario inexistente
            id_invalido = -2147483647

            cursor.execute(
                "SELECT id_usuario FROM usuarios "
                "WHERE id_usuario = %s",
                (id_invalido,),
            )
            assert cursor.fetchone() is None

            with pytest.raises(
                pymysql.err.IntegrityError
            ) as erro:
                cursor.execute(
                    """
                    INSERT INTO moradores
                        (id_casa, id_usuario, perfil)
                    VALUES (%s, %s, %s)
                    """,
                    (id_casa_a, id_invalido, "comum"),
                )

            assert erro.value.args[0] == 1452

            # 6. Impedir casa inexistente
            cursor.execute(
                "SELECT id_casa FROM casas "
                "WHERE id_casa = %s",
                (id_invalido,),
            )
            assert cursor.fetchone() is None

            with pytest.raises(
                pymysql.err.IntegrityError
            ) as erro:
                cursor.execute(
                    """
                    INSERT INTO moradores
                        (id_casa, id_usuario, perfil)
                    VALUES (%s, %s, %s)
                    """,
                    (id_invalido, id_comum, "comum"),
                )

            assert erro.value.args[0] == 1452

            # 7. Impedir vinculo duplicado
            with pytest.raises(
                pymysql.err.IntegrityError
            ) as erro:
                cursor.execute(
                    """
                    INSERT INTO moradores
                        (id_casa, id_usuario, perfil)
                    VALUES (%s, %s, %s)
                    """,
                    (id_casa_a, id_admin, "comum"),
                )

            assert erro.value.args[0] == 1062

    finally:
        # Desfaz todos os cadastros de teste
        conexao.rollback()
        conexao.close()


