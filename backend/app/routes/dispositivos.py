from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

from app.models.dispositivo import TIPOS
from app.permissoes import administrador_obrigatorio, login_obrigatorio
from app.services import dispositivos as servico
from app.services.comodos import transferir_dispositivo

dispositivos = Blueprint("dispositivos", __name__)


def pedido_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@dispositivos.get("/dispositivos")
@login_obrigatorio
def listar():
    return render_template("dispositivos.html", tipos=TIPOS,
                           ajustes=servico.ajustes_por_tipo(),
                           **servico.dados_da_pagina(g.casa_id))


@dispositivos.post("/dispositivos")
@administrador_obrigatorio
def criar():
    try:
        servico.cadastrar_dispositivo(g.casa_id, request.form.get("nome"),
                                      request.form.get("tipo"), request.form.get("id_comodo"))
        flash("Dispositivo cadastrado.", "sucesso")
    except ValueError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("dispositivos.listar"))


@dispositivos.post("/dispositivos/<int:id_dispositivo>/controle")
@login_obrigatorio
def controlar(id_dispositivo):
    if not g.usuario.pode_controlar_dispositivo():
        return jsonify({"erro": "Sem permissao."}), 403
    try:
        resultado = servico.alterar_dispositivo(
            id_dispositivo, g.casa_id, g.usuario.id_usuario,
            request.form.get("acao", ""), request.form.get("valor"),
        )
        if pedido_ajax():
            return jsonify({"ok": True, "resultado": resultado})
        flash("Controle atualizado.", "sucesso")
    except ValueError as erro:
        if pedido_ajax():
            return jsonify({"erro": str(erro)}), 400
        flash(str(erro), "erro")
    return redirect(url_for("dispositivos.listar"))


@dispositivos.post("/dispositivos/<int:id_dispositivo>/transferir")
@administrador_obrigatorio
def transferir(id_dispositivo):
    id_comodo = request.form.get("id_comodo", "")
    if not id_comodo.isdigit():
        flash("Escolha o comodo de destino.", "erro")
        return redirect(url_for("dispositivos.listar"))
    try:
        nome, destino = transferir_dispositivo(
            g.casa_id, id_dispositivo, int(id_comodo), g.usuario.id_usuario
        )
        flash(f"{nome} agora esta em {destino}.", "sucesso")
    except ValueError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("dispositivos.listar"))


@dispositivos.post("/dispositivos/<int:id_dispositivo>/remover")
@administrador_obrigatorio
def remover(id_dispositivo):
    try:
        servico.remover_dispositivo(g.casa_id, id_dispositivo)
        flash("Dispositivo removido da lista. O historico foi preservado.", "sucesso")
    except ValueError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("dispositivos.listar"))
