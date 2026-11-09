-- Banco de dados do Habitus - Smart Home 2050
-- Projeto ExpoTech 2026.2
-- MySQL 8.0.16 ou superior

CREATE DATABASE IF NOT EXISTS habitus_smart_home
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE habitus_smart_home;

-- 1. Pessoas que podem entrar no sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    -- 1 = entrou com senha temporaria e precisa troca-la no primeiro acesso
    trocar_senha BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Casas cadastradas no sistema
CREATE TABLE IF NOT EXISTS casas (
    id_casa INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    endereco VARCHAR(200),
    criada_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Quem mora em cada casa e qual permissao possui
CREATE TABLE IF NOT EXISTS moradores (
    id_morador INT AUTO_INCREMENT PRIMARY KEY,
    id_casa INT NOT NULL,
    id_usuario INT NOT NULL,
    perfil ENUM('administrador', 'comum') NOT NULL DEFAULT 'comum',

    UNIQUE (id_casa, id_usuario),
    FOREIGN KEY (id_casa) REFERENCES casas(id_casa) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- 4. Ambientes da casa, como sala e quarto
-- A collation utf8mb4_unicode_ci faz o UNIQUE ignorar maiusculas: 'Sala' = 'SALA'.
CREATE TABLE IF NOT EXISTS comodos (
    id_comodo INT AUTO_INCREMENT PRIMARY KEY,
    id_casa INT NOT NULL,
    nome VARCHAR(80) NOT NULL,

    UNIQUE (id_casa, nome),
    FOREIGN KEY (id_casa) REFERENCES casas(id_casa) ON DELETE CASCADE
);

-- 5. Dispositivos simulados ou conectados
CREATE TABLE IF NOT EXISTS dispositivos (
    id_dispositivo INT AUTO_INCREMENT PRIMARY KEY,
    id_comodo INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    tipo ENUM('luz', 'ar_condicionado', 'aquecedor', 'ventilador', 'outro') NOT NULL,
    ligado BOOLEAN NOT NULL DEFAULT FALSE,
    brilho TINYINT UNSIGNED DEFAULT NULL,
    temperatura DECIMAL(4,1) DEFAULT NULL,
    intensidade TINYINT UNSIGNED DEFAULT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    -- RESTRICT: um comodo com dispositivos nunca e apagado (nem os dispositivos junto).
    CONSTRAINT fk_dispositivos_comodo
        FOREIGN KEY (id_comodo) REFERENCES comodos(id_comodo) ON DELETE RESTRICT,
    CHECK (brilho IS NULL OR brilho BETWEEN 0 AND 100),
    CHECK (intensidade IS NULL OR intensidade BETWEEN 0 AND 100),
    CHECK (temperatura IS NULL OR temperatura BETWEEN 16 AND 30)
);

-- 6. Registro do que foi alterado nos dispositivos
CREATE TABLE IF NOT EXISTS historico (
    id_historico INT AUTO_INCREMENT PRIMARY KEY,
    id_dispositivo INT NOT NULL,
    id_usuario INT DEFAULT NULL,
    acao VARCHAR(60) NOT NULL,
    valor_anterior VARCHAR(50),
    valor_novo VARCHAR(50),
    data_acao DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_dispositivo) REFERENCES dispositivos(id_dispositivo) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE SET NULL
);

-- 7. Acoes programadas para executar em determinados horarios
CREATE TABLE IF NOT EXISTS rotinas (
    id_rotina INT AUTO_INCREMENT PRIMARY KEY,
    id_dispositivo INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    acao ENUM('ligar', 'desligar', 'ajustar_brilho',
              'ajustar_temperatura', 'ajustar_intensidade') NOT NULL,
    valor DECIMAL(5,1) DEFAULT NULL,
    horario TIME NOT NULL,
    dias_semana VARCHAR(30) NOT NULL DEFAULT 'todos',
    ativa BOOLEAN NOT NULL DEFAULT TRUE,
    ultima_execucao DATETIME DEFAULT NULL,

    FOREIGN KEY (id_dispositivo) REFERENCES dispositivos(id_dispositivo) ON DELETE CASCADE
);

-- Confira se as sete tabelas foram criadas.
SHOW TABLES;

-- Exemplos para usar depois que o cadastro do usuario estiver funcionando:
-- O backend deve gerar o hash da senha e criar o usuario.
-- INSERT INTO casas (nome) VALUES ('Minha casa');
-- INSERT INTO moradores (id_casa, id_usuario, perfil) VALUES (1, 1, 'administrador');
-- INSERT INTO comodos (id_casa, nome) VALUES (1, 'Sala'), (1, 'Quarto');
-- INSERT INTO dispositivos (id_comodo, nome, tipo, brilho)
-- VALUES (1, 'Luz da sala', 'luz', 80);
-- INSERT INTO dispositivos (id_comodo, nome, tipo, temperatura)
-- VALUES (2, 'Ar-condicionado do quarto', 'ar_condicionado', 23.0);
-- INSERT INTO rotinas (id_dispositivo, nome, acao, horario)
-- VALUES (1, 'Ligar a luz de manha', 'ligar', '07:00:00');
