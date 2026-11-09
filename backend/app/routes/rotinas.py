from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.models.rotina import ACOES, DIAS_DA_SEMANA, TODOS_OS_DIAS
from app.permissoes import administrador_obrigatorio, login_obrigatorio
from app.services import rotinas as servico

rotinas = Blueprint("rotinas", __name__)

# Valores iniciais do formulario de nova rotina.
FORMULARIO_PADRAO = {
    "nome": "", "id_dispositivo": None, "acao": "ligar", "valor": "",
    "horario": "19:00", "dias": TODOS_OS_DIAS,
}


def mostrar_pagina(formulario=None, editando=None, status=200):
    """Monta a pagina. `editando` e o id da rotina aberta no formulario."""
    return render_template(
        "rotinas.html",
        formulario=formulario or FORMULARIO_PADRAO,
        editando=editando,
        acoes=ACOES,
        dias_da_semana=DIAS_DA_SEMANA,
        **servico.dados_da_pagina(g.casa_id),
    ), status


def formulario_enviado():
    """Campos como vieram do navegador, para reapresentar se houver erro."""
    id_dispositivo = request.form.get("id_dispositivo", "")
    return {
        "nome": request.form.get("nome", ""),
        "id_dispositivo": int(id_dispositivo) if id_dispositivo.isdigit() else None,
        "acao": request.form.get("acao", ""),
        "valor": request.form.get("valor", ""),
        "horario": request.form.get("horario", ""),
        "dias": set(request.form.getlist("dias")),
    }


def salvar(id_rotina=None):
    formulario = formulario_enviado()
    try:
        servico.salvar_rotina(g.casa_id, formulario, id_rotina)
    except ValueError as erro:
        # Mostra a pagina de novo com o que a pessoa digitou.
        flash(str(erro), "erro")
        return mostrar_pagina(formulario, editando=id_rotina, status=400)
    if id_rotina is None:
        flash("Rotina criada. Ela sera executada no horario programado.", "sucesso")
    else:
        flash("Rotina atualizada.", "sucesso")
    return redirect(url_for("rotinas.listar"))


@rotinas.get("/rotinas")
@login_obrigatorio
def listar():
    return mostrar_pagina()


@rotinas.post("/rotinas")
@administrador_obrigatorio
def criar():
    return salvar()


@rotinas.get("/rotinas/<int:id_rotina>/editar")
@administrador_obrigatorio
def editar(id_rotina):
    rotina = servico.buscar_rotina(g.casa_id, id_rotina)
    if rotina is None:
        abort(404, description="Rotina nao encontrada nesta casa.")
    formulario = {
        "nome": rotina.nome, "id_dispositivo": rotina.id_dispositivo,
        "acao": rotina.acao, "valor": rotina.valor_formulario,
        "horario": rotina.horario, "dias": rotina.dias,
    }
    return mostrar_pagina(formulario, editando=id_rotina)


@rotinas.post("/rotinas/<int:id_rotina>/editar")
@administrador_obrigatorio
def atualizar(id_rotina):
    return salvar(id_rotina)


@rotinas.post("/rotinas/<int:id_rotina>/alternar")
@administrador_obrigatorio
def alternar(id_rotina):
    try:
        servico.alternar_rotina(g.casa_id, id_rotina)
        flash("Rotina atualizada.", "sucesso")
    except ValueError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("rotinas.listar"))


@rotinas.post("/rotinas/<int:id_rotina>/remover")
@administrador_obrigatorio
def remover(id_rotina):
    try:
        servico.remover_rotina(g.casa_id, id_rotina)
        flash("Rotina removida.", "sucesso")
    except ValueError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("rotinas.listar"))
