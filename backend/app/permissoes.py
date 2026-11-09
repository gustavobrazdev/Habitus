from functools import wraps

from flask import abort, g, redirect, url_for


def login_obrigatorio(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        if not g.usuario:
            return redirect(url_for("auth.entrar"))
        return funcao(*args, **kwargs)
    return verificar


def administrador_obrigatorio(funcao):
    @wraps(funcao)
    @login_obrigatorio
    def verificar(*args, **kwargs):
        if not g.usuario.pode_gerenciar():
            abort(403, description="Somente o administrador pode fazer isso.")
        return funcao(*args, **kwargs)
    return verificar
