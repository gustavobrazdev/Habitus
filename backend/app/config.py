import os
from pathlib import Path

from dotenv import load_dotenv

PASTA_BACKEND = Path(__file__).resolve().parent.parent
PASTA_PROJETO = PASTA_BACKEND.parent
PASTA_FRONTEND = PASTA_PROJETO / "frontend"

# Procura o .env primeiro em backend/ e depois na raiz do projeto.
for arquivo_env in (PASTA_BACKEND / ".env", PASTA_PROJETO / ".env"):
    if arquivo_env.exists():
        load_dotenv(arquivo_env)
        break


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "chave-local-apenas-para-testes")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "habitus_smart_home")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
