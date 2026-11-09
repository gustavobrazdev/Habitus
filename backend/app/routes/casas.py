from flask import (
    Blueprint, flash, g, make_response, redirect, render_template, request, session, url_for,
)

from app.permissoes import administrador_obrigatorio, login_obrigatorio
from app.services import comodos as servico_comodos
from app.services import moradores as servico_moradores
from app.services.casas import casas_do_usuario, pode_abrir_casa

casas = Blueprint("casas", __name__)


def mostrar_casa(**extras):
    return render_template(
        "casa.html",
        comodos=servico_comodos.listar_comodos(g.casa_id),
        moradores=servico_moradores.listar_moradores(g.casa_id),
        minhas_casas=casas_do_usuario(g.usuario.id_usuario),
        **extras,
    )


def voltar_com_resultado(acao, mensagem_sucesso):
    """Executa a acao do servico e mostra a mensagem de sucesso ou o erro."""
    try:
        resultado = acao()
        flash(mensagem_sucesso(resultado) if callable(mensagem_sucesso) else mensagem_sucesso,
              "sucesso")
    except ValueError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("casas.detalhes"))


@casas.get("/casa")
@login_obrigatorio
def detalhes():
    return mostrar_casa()


@casas.post("/casa/selecionar")
@login_obrigatorio
def selecionar():
    id_casa = request.form.get("id_casa", "")
    if id_casa.isdigit() and pode_abrir_casa(g.usuario.id_usuario, int(id_casa)):
        session["casa_id"] = int(id_casa)
        return redirect(url_for("site.painel"))
    flash("Voce nao tem acesso a essa casa.", "erro")
    return redirect(url_for("casas.detalhes"))


@casas.post("/casa/comodos")
@administrador_obrigatorio
def novo_comodo():
    return voltar_com_resultado(
        lambda: servico_comodos.criar_comodo(g.casa_id, request.form.get("nome", "")),
        lambda comodo: f"Comodo {comodo.nome} cadastrado.",
    )


@casas.post("/casa/comodos/<int:id_comodo>/renomear")
@administrador_obrigatorio
def renomear_comodo(id_comodo):
    return voltar_com_resultado(
        lambda: servico_comodos.renomear_comodo(g.casa_id, id_comodo, request.form.get("nome", "")),
        lambda comodo: f"Comodo renomeado para {comodo.nome}.",
    )


@casas.post("/casa/comodos/<int:id_comodo>/remover")
@administrador_obrigatorio
def remover_comodo(id_comodo):
    return voltar_com_resultado(
        lambda: servico_comodos.excluir_comodo(g.casa_id, id_comodo),
        lambda nome: f"Comodo {nome} excluido.",
    )


@casas.post("/casa/moradores")
@administrador_obrigatorio
def novo_morador():
    try:
        morador = servico_moradores.cadastrar_morador(
            g.casa_id, request.form.get("nome", ""),
            request.form.get("email", ""), request.form.get("perfil", ""),
        )
    except ValueError as erro:
        flash(str(erro), "erro")
        return redirect(url_for("casas.detalhes"))

    if morador["senha_temporaria"] is None:
        flash(f"{morador['nome']} ja tinha conta e agora participa desta casa.", "sucesso")
        return redirect(url_for("casas.detalhes"))

    # A senha aparece so nesta resposta: nao fica na sessao nem no cache do navegador.
    flash(f"Conta de {morador['nome']} criada e vinculada a casa.", "sucesso")
    resposta = make_response(mostrar_casa(novo_morador=morador))
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@casas.post("/casa/moradores/<int:id_morador>/perfil")
@administrador_obrigatorio
def mudar_perfil(id_morador):
    return voltar_com_resultado(
        lambda: servico_moradores.mudar_perfil(
            g.casa_id, id_morador, request.form.get("perfil", ""), g.usuario.id_usuario),
        "Permissao atualizada.",
    )


@casas.post("/casa/moradores/<int:id_morador>/remover")
@administrador_obrigatorio
def remover_morador(id_morador):
    return voltar_com_resultado(
        lambda: servico_moradores.remover_morador(g.casa_id, id_morador, g.usuario.id_usuario),
        "Acesso removido.",
    )
