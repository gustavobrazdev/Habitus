from flask import Blueprint, g, render_template

from app.permissoes import login_obrigatorio
from app.services.casas import historico_da_casa

historico = Blueprint("historico", __name__)


@historico.get("/historico")
@login_obrigatorio
def listar():
    return render_template("historico.html", eventos=historico_da_casa(g.casa_id))
