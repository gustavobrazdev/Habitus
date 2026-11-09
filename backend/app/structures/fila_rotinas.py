"""Fila de prioridade (heapq) para os horarios e fila FIFO (deque) para os comandos."""

import heapq
from collections import deque

from app.models.rotina import proximo_horario


class FilaRotinas:
    """Organiza as rotinas pelo proximo horario em que devem rodar.

    A chave do heap e a data/hora da proxima execucao depois de `desde`
    (o momento da verificacao anterior). Assim o topo do heap e sempre a
    rotina mais proxima, e nenhuma rotina entre `desde` e `agora` e perdida,
    mesmo que a verificacao atrase ou passe da meia-noite.
    """

    def __init__(self, rotinas, desde):
        self._heap = []
        for rotina in rotinas:
            agendado = proximo_horario(rotina["horario"], desde)
            # id_rotina desempata horarios iguais (dicionarios nao podem ser comparados).
            heapq.heappush(self._heap, (agendado, rotina["id_rotina"], rotina))

    def __len__(self):
        return len(self._heap)

    def proxima(self):
        """Data e hora da proxima rotina, sem retira-la da fila."""
        return self._heap[0][0] if self._heap else None

    def comandos_ate(self, agora, deve_executar):
        """Retira do heap tudo que ja chegou na hora e devolve uma fila FIFO,
        em ordem de horario, com pares (rotina, horario agendado)."""
        comandos = deque()
        while self._heap and self._heap[0][0] <= agora:
            agendado, _, rotina = heapq.heappop(self._heap)
            if deve_executar(rotina, agendado):
                comandos.append((rotina, agendado))
        return comandos
