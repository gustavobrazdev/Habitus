import hmac
import secrets

from flask import Flask, abort, g, redirect, request, session, url_for

from app.config import PASTA_FRONTEND, Config
from app.models.rotina import formatar_numero
from app.models.usuario import Usuario
from app.services.autenticacao import carregar_acesso


def criar_app(configuracoes=None):
    app = Flask(
        __name__,
        template_folder=str(PASTA_FRONTEND / "templates"),
        static_folder=str(PASTA_FRONTEND / "static"),
    )
    app.config.from_object(Config)
    if configuracoes:
        app.config.update(configuracoes)

    @app.before_request
    def carregar_usuario():
        g.usuario = None
        g.casa_id = None
        g.nome_casa = None
        id_usuario = session.get("usuario_id")
        if not id_usuario:
            return
        acesso = carregar_acesso(id_usuario, session.get("casa_id"))
        if acesso is None:
            session.clear()
            return
        session["casa_id"] = acesso["id_casa"]
        g.usuario = Usuario(acesso["id_usuario"], acesso["nome"], acesso["perfil"])
        g.casa_id = acesso["id_casa"]
        g.nome_casa = acesso["nome_casa"]

    @app.before_request
    def exigir_troca_de_senha():
        # Quem entrou com senha temporaria so acessa a troca de senha ou sai.
        liberadas = ("auth.trocar_senha", "auth.sair", "static")
        if g.usuario and session.get("trocar_senha") and request.endpoint not in liberadas:
            return redirect(url_for("auth.trocar_senha"))

    @app.before_request
    def proteger_formularios():
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
            esperado = session.get("csrf_token", "")
            if not token or not esperado or not hmac.compare_digest(token, esperado):
                abort(400, description="Sessao expirada. Atualize a pagina e tente de novo.")

    @app.context_processor
    def dados_tela():
        def token_csrf():
            if "csrf_token" not in session:
                session["csrf_token"] = secrets.token_hex(24)
            return session["csrf_token"]

        return {"csrf_token": token_csrf}

    # Filtro {{ valor|numero }}: 22.0 -> 22 e 22.5 -> 22,5
    app.jinja_env.filters["numero"] = formatar_numero

    from app.routes.autenticacao import auth
    from app.routes.casas import casas
    from app.routes.dispositivos import dispositivos
    from app.routes.historico import historico
    from app.routes.rotinas import rotinas
    from app.routes.site import site

    for blueprint in (auth, site, casas, dispositivos, rotinas, historico):
        app.register_blueprint(blueprint)

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def pagina_erro(erro):
        return (
            f"<h2>{erro.code} - {erro.description}</h2>"
            "<p><a href='/'>Voltar ao Habitus</a></p>",
            erro.code,
        )

    return app
