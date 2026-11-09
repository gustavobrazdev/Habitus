-- Migracao do gerenciamento de comodos (renomear, excluir e transferir dispositivos).
-- Execute SOMENTE se o seu banco foi criado antes desta versao.
-- Nenhum dado e apagado: apenas a regra da chave estrangeira muda de
-- ON DELETE CASCADE para ON DELETE RESTRICT, para que excluir um comodo
-- nunca remova dispositivos, rotinas ou historico junto.

USE habitus_smart_home;

-- 1. Confira o nome atual da chave estrangeira (normalmente dispositivos_ibfk_1):
SELECT CONSTRAINT_NAME, DELETE_RULE
FROM information_schema.REFERENTIAL_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'habitus_smart_home'
  AND TABLE_NAME = 'dispositivos'
  AND REFERENCED_TABLE_NAME = 'comodos';

-- 2. Se o nome mostrado for diferente, troque dispositivos_ibfk_1 abaixo.
ALTER TABLE dispositivos DROP FOREIGN KEY dispositivos_ibfk_1;

ALTER TABLE dispositivos
    ADD CONSTRAINT fk_dispositivos_comodo
    FOREIGN KEY (id_comodo) REFERENCES comodos(id_comodo) ON DELETE RESTRICT;

-- 3. Confira: DELETE_RULE deve aparecer como RESTRICT.
SELECT CONSTRAINT_NAME, DELETE_RULE
FROM information_schema.REFERENTIAL_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'habitus_smart_home'
  AND TABLE_NAME = 'dispositivos'
  AND REFERENCED_TABLE_NAME = 'comodos';
