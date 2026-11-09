-- Migracao do cadastro de moradores com senha temporaria.
-- Execute SOMENTE se o seu banco foi criado antes desta versao.
-- Nenhum dado e apagado: apenas uma coluna nova e adicionada em `usuarios`.
-- Os usuarios que ja existem ficam com trocar_senha = 0 (nada muda para eles).

USE habitus_smart_home;

ALTER TABLE usuarios
    ADD COLUMN trocar_senha BOOLEAN NOT NULL DEFAULT FALSE AFTER senha_hash;

-- Confira: a coluna trocar_senha deve aparecer na lista.
SHOW COLUMNS FROM usuarios;
