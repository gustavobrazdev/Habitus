// Pequenas interacoes das telas. As regras continuam no Python.

document.querySelectorAll(".mostrar-senha-figma").forEach((botao) => {
    botao.addEventListener("click", () => {
        const campo = botao.previousElementSibling;
        campo.type = campo.type === "password" ? "text" : "password";
        botao.classList.toggle("ativo", campo.type === "text");
        botao.setAttribute("aria-label", campo.type === "text" ? "Ocultar senha" : "Mostrar senha");
    });
});

const avisoContaCriada = [...document.querySelectorAll(".aviso")].find((aviso) =>
    aviso.textContent.includes("Conta criada!")
);
if (avisoContaCriada) {
    const popup = document.createElement("div");
    popup.className = "popup-conta";
    popup.innerHTML = `
        <div class="popup-conta-caixa" role="dialog" aria-modal="true" aria-labelledby="titulo-popup-conta">
            <div class="popup-icone">✓</div>
            <h2 id="titulo-popup-conta">Conta criada</h2>
            <p>Sua casa e sua conta estão prontas para uso.</p>
            <button type="button">Continuar</button>
        </div>`;
    document.body.appendChild(popup);
    popup.querySelector("button").addEventListener("click", () => popup.remove());
}

document.querySelectorAll('input[type="range"]').forEach((campo) => {
    campo.addEventListener("input", () => {
        const texto = campo.closest("label").querySelector("[data-valor]");
        texto.textContent = campo.value + (campo.dataset.unidade || "");
    });
});

document.querySelectorAll("form[data-confirmar]").forEach((formulario) => {
    formulario.addEventListener("submit", (evento) => {
        if (!window.confirm(formulario.dataset.confirmar)) {
            evento.preventDefault();
        }
    });
});

document.querySelectorAll("form[data-ajax]").forEach((formulario) => {
    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const botao = formulario.querySelector('button[type="submit"]');
        botao.disabled = true;
        try {
            const resposta = await fetch(formulario.action, {
                method: "POST",
                body: new FormData(formulario),
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            const dados = await resposta.json();
            if (!resposta.ok) {
                throw new Error(dados.erro || "Nao foi possivel salvar.");
            }
            window.location.reload();
        } catch (erro) {
            window.alert(erro.message);
            botao.disabled = false;
        }
    });
});

const botaoMenu = document.querySelector("#abrir-menu");
if (botaoMenu) {
    botaoMenu.addEventListener("click", () => {
        document.querySelector("#menu-lateral").classList.toggle("aberto");
    });
}

// O formulario de rotina mostra apenas os controles compativeis com o dispositivo.
const seletorDispositivo = document.querySelector("#tipo-dispositivo");
const seletorAcao = document.querySelector("#acao-rotina");
const campoValor = document.querySelector("#valor-rotina");

if (seletorDispositivo && seletorAcao && campoValor) {
    const caixaValor = document.querySelector("#campo-valor");
    const tituloValor = document.querySelector("#titulo-valor");
    const textoValor = caixaValor.querySelector("[data-valor]");

    // Limites e unidades vem das classes Python (atributo `ajuste` de cada dispositivo).
    const ajustes = JSON.parse(seletorAcao.form.dataset.ajustes || "{}");
    // Na edicao, o valor salvo so e usado enquanto a acao original continuar escolhida.
    const acaoOriginal = seletorAcao.value;
    let acaoAnterior = null;

    const ajustarOpcoes = () => {
        // Cada dispositivo informa as acoes que a sua classe aceita.
        const permitidas = (seletorDispositivo.selectedOptions[0]?.dataset.acoes || "ligar desligar").split(" ");
        for (const opcao of seletorAcao.options) {
            opcao.hidden = !permitidas.includes(opcao.value);
            opcao.disabled = opcao.hidden;
        }
        if (seletorAcao.selectedOptions[0]?.disabled) {
            seletorAcao.value = "ligar";
        }

        const ajuste = ajustes[seletorAcao.value];
        caixaValor.hidden = !ajuste;
        campoValor.disabled = !ajuste; // campo desativado nao e enviado
        if (ajuste && seletorAcao.value !== acaoAnterior) {
            tituloValor.textContent = ajuste.titulo;
            campoValor.min = ajuste.minimo;
            campoValor.max = ajuste.maximo;
            campoValor.step = ajuste.passo;
            campoValor.dataset.unidade = ajuste.unidade;
            // Comeca no valor salvo (edicao) ou no meio da faixa: 50% ou 23 °C.
            const salvo = campoValor.dataset.salvo;
            const meio = (ajuste.minimo + ajuste.maximo) / 2;
            campoValor.value = seletorAcao.value === acaoOriginal && salvo !== "" ? salvo : meio;
            textoValor.textContent = campoValor.value + ajuste.unidade;
        }
        acaoAnterior = seletorAcao.value;
    };
    seletorDispositivo.addEventListener("change", ajustarOpcoes);
    seletorAcao.addEventListener("change", ajustarOpcoes);
    ajustarOpcoes();
}
