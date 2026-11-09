from flask import Blueprint, g, redirect, render_template, url_for

from app.permissoes import login_obrigatorio
from app.services.casas import resumo_do_painel

site = Blueprint("site", __name__)


@site.get("/")
def inicio():
    return redirect(url_for("site.painel") if g.usuario else url_for("auth.entrar"))


@site.get("/painel")
@login_obrigatorio
def painel():
    return render_template("painel.html", **resumo_do_painel(g.casa_id))
