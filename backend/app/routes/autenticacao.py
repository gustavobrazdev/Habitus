from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from app.services.autenticacao import autenticar, cadastrar_conta, trocar_senha_temporaria

auth = Blueprint("auth", __name__)


@auth.route("/entrar", methods=["GET", "POST"])
def entrar():
    if g.usuario:
        return redirect(url_for("site.painel"))
    if request.method == "POST":
        usuario = autenticar(request.form.get("email"), request.form.get("senha"))
        if not usuario:
            flash("E-mail ou senha incorretos.", "erro")
        else:
            session.clear()
            session["usuario_id"] = usuario["id_usuario"]
            # .get() mantem o login funcionando mesmo antes da migracao do banco.
            if usuario.get("trocar_senha"):
                session["trocar_senha"] = True
                return redirect(url_for("auth.trocar_senha"))
            return redirect(url_for("site.painel"))
    return render_template("entrar.html")


@auth.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if g.usuario:
        return redirect(url_for("site.painel"))
    if request.method == "POST":
        try:
            conta = cadastrar_conta(request.form)
        except ValueError as erro:
            flash(str(erro), "erro")
            return render_template("cadastro.html")
        session.clear()
        session["usuario_id"] = conta["id_usuario"]
        session["casa_id"] = conta["id_casa"]
        if conta["opcao_comodos"] == "vazio":
            flash("Conta criada! Cadastre os comodos da sua casa em Minha casa.", "sucesso")
        else:
            flash("Conta criada! Sua casa esta pronta para testar.", "sucesso")
        return redirect(url_for("site.painel"))
    return render_template("cadastro.html")


@auth.route("/trocar-senha", methods=["GET", "POST"])
def trocar_senha():
    if not g.usuario:
        return redirect(url_for("auth.entrar"))
    if not session.get("trocar_senha"):
        return redirect(url_for("site.painel"))
    if request.method == "POST":
        try:
            trocar_senha_temporaria(g.usuario.id_usuario, request.form.get("senha", ""),
                                    request.form.get("confirmacao", ""))
        except ValueError as erro:
            flash(str(erro), "erro")
            return render_template("trocar_senha.html")
        session.pop("trocar_senha", None)
        flash("Senha alterada. Bem-vindo ao Habitus!", "sucesso")
        return redirect(url_for("site.painel"))
    return render_template("trocar_senha.html")


@auth.post("/sair")
def sair():
    session.clear()
    return redirect(url_for("auth.entrar"))
