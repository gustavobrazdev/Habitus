"""Classe que representa um ambiente (comodo) da casa."""

from app.validators.casas import validar_nome_comodo


# Sugestao oferecida no cadastro. A tupla evita alteracoes acidentais.
COMODOS_SUGERIDOS = ("Sala", "Quarto", "Cozinha")


class Comodo:
    """Guarda o nome ja validado e sabe comparar nomes sem diferenciar maiusculas."""

    def __init__(self, nome, id_comodo=None):
        self.id_comodo = id_comodo
        self._nome = validar_nome_comodo(nome)

    @property
    def nome(self):
        return self._nome

    @property
    def chave(self):
        """Versao do nome usada para comparar: 'SALA', 'sala' e ' Sala ' sao iguais."""
        return self._nome.casefold()

    def tem_mesmo_nome(self, outro_nome):
        return self.chave == " ".join(str(outro_nome or "").split()).casefold()
