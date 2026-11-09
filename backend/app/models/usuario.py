class Usuario:
    """Representa as permissoes de uma pessoa dentro de uma casa."""

    PERFIS = ("administrador", "comum")

    def __init__(self, id_usuario, nome, perfil):
        self.id_usuario = id_usuario
        self.nome = nome
        self._perfil = perfil

    @property
    def perfil(self):
        return self._perfil

    def pode_gerenciar(self):
        return self._perfil == "administrador"

    def pode_controlar_dispositivo(self):
        return self._perfil in ("administrador", "comum")

