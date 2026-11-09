"""Execute este arquivo em OUTRO terminal para ativar as rotinas."""

import time
from datetime import datetime

from app import criar_app
from app.services.rotinas import executar_pendentes

INTERVALO_SEGUNDOS = 20

app = criar_app()

if __name__ == "__main__":
    print(f"Verificando rotinas a cada {INTERVALO_SEGUNDOS} segundos. Ctrl+C para sair.")
    ultima_verificacao = None
    try:
        while True:
            agora = datetime.now()
            with app.app_context():
                try:
                    # Passa a verificacao anterior para nao perder rotinas entre as duas.
                    executadas, falhas = executar_pendentes(agora, ultima_verificacao)
                    ultima_verificacao = agora
                    for nome in executadas:
                        print(f"{agora:%H:%M:%S} Rotina executada: {nome}")
                    for falha in falhas:
                        print(f"{agora:%H:%M:%S} Rotina com erro: {falha}")
                except Exception as erro:
                    # Ex.: MySQL fora do ar. A proxima verificacao tenta de novo
                    # a partir da ultima que deu certo.
                    print(f"{agora:%H:%M:%S} Erro ao verificar rotinas: {erro}")
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        print("Execucao encerrada.")
