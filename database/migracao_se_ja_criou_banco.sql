-- Execute SOMENTE se voce ja rodou a versao anterior do banco.
-- Se criou o banco usando database/schema.sql deste projeto, NAO rode.

USE habitus_smart_home;
ALTER TABLE rotinas ADD COLUMN ultima_execucao DATETIME DEFAULT NULL;
