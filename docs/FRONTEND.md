# Front-end do Habitus

Este documento descreve o front-end **realmente implementado** no Habitus: a organização de `frontend/`, os templates Jinja2, as telas, o CSS e o JavaScript. Também explica como a interface conversa com o back-end e quais cuidados de segurança ela aplica.

Assuntos relacionados em outros documentos:

- rotas e permissões de cada tela: [ROTAS_E_PERMISSOES.md](ROTAS_E_PERMISSOES.md#3-rotas-por-blueprint);
- CSRF, sessão e escape em detalhe: [AUTENTICACAO_E_SEGURANCA.md](AUTENTICACAO_E_SEGURANCA.md);
- guia de design para o Figma: [TELAS_FIGMA.md](TELAS_FIGMA.md).

## Sumário

1. [Organização](#1-organização)
2. [Templates e Jinja2](#2-templates-e-jinja2)
3. [Telas do sistema](#3-telas-do-sistema)
4. [CSS e responsividade](#4-css-e-responsividade)
5. [JavaScript](#5-javascript)
6. [Comunicação com o back-end: controle de um dispositivo](#6-comunicação-com-o-back-end-controle-de-um-dispositivo)
7. [Segurança na interface](#7-segurança-na-interface)
8. [Implementação, planejamento visual e Figma](#8-implementação-planejamento-visual-e-figma)
9. [Limitações e pontos a testar no navegador](#9-limitações-e-pontos-a-testar-no-navegador)
10. [Estado da verificação e fontes](#10-estado-da-verificação-e-fontes)

---

## 1. Organização

```text
frontend/
├── templates/
│   ├── base.html            # Estrutura comum: menu, barra superior, mensagens, script
│   ├── entrar.html          # Login
│   ├── cadastro.html        # Cadastro de conta e casa
│   ├── trocar_senha.html    # Troca obrigatória da senha temporária
│   ├── painel.html          # Painel principal
│   ├── casa.html            # Minha casa: cômodos, moradores, troca de casa
│   ├── dispositivos.html    # Lista e controles de dispositivos
│   ├── rotinas.html         # Formulário e lista de rotinas
│   └── historico.html       # Tabela de alterações
└── static/
    ├── css/estilo.css       # Único arquivo de estilos (350 linhas)
    ├── js/app.js            # Único arquivo JavaScript (121 linhas)
    └── img/sala-habitus.png # Ilustração das telas de login e cadastro
```

- **Não é um servidor separado:** não há `package.json`, npm, framework JavaScript nem etapa de build.
- **Quem serve os arquivos:** `criar_app()` (`backend/app/__init__.py`) configura o Flask com `template_folder` em `frontend/templates` e `static_folder` em `frontend/static`. Os templates são renderizados no servidor com `render_template()`, e os arquivos estáticos são servidos em `/static/...`.
- **Pasta `img/`:** contém também um `.gitkeep`, que só mantém a pasta no controle de versão.

## 2. Templates e Jinja2

### 2.1 O template base

Todas as oito páginas começam com `{% extends 'base.html' %}` e preenchem dois blocos: `titulo` (texto da aba, seguido de " | Smart Home") e `conteudo`.

`base.html` decide qual estrutura mostrar:

```jinja
{% set mostrar_menu = g.usuario and not session.get('trocar_senha') %}
<body class="{% if mostrar_menu %}com-sistema{% else %}sem-sistema{% endif %}">
```

| Situação | Estrutura |
| --- | --- |
| Logado, sem troca de senha pendente (`com-sistema`) | Menu lateral, barra superior e área de conteúdo |
| Visitante ou com troca pendente (`sem-sistema`) | Apenas o conteúdo centralizado (telas de acesso) |

Elementos comuns do `base.html`:

- **Menu lateral:**
  - a marca "habitus";
  - o nome da casa aberta (`g.nome_casa`);
  - os links Painel, Dispositivos, Rotinas, Histórico e Minha casa, com o item atual destacado por `request.endpoint` ou `request.blueprint`;
  - o nome e o perfil da pessoa;
  - o formulário "Sair da conta".
- **Barra superior:** o botão de menu (☰), o texto "Ambiente de demonstração • Dispositivos simulados" e a etiqueta "● Sistema local".
- **Mensagens `flash`**, exibidas com a categoria como classe CSS (`aviso sucesso`, `aviso erro`).
- **O script** `js/app.js`, carregado com `defer` em todas as páginas.

### 2.2 Recursos do Jinja2 usados

| Recurso | Exemplo no Habitus |
| --- | --- |
| Herança de templates | `{% extends 'base.html' %}`, `{% block conteudo %}` |
| Laços com caso vazio | `{% for dispositivo in dispositivos %} … {% else %}Nenhum dispositivo…{% endfor %}` |
| Laço com filtro | `{% for comodo in comodos if comodo.id_comodo != dispositivo.id_comodo %}` (opções de "Mover para") |
| Condicionais | `{% if g.usuario.pode_gerenciar() %}` |
| Variáveis locais | `{% set ajuste = ajustes[dispositivo.tipo] %}` |
| Filtros | `length`, `lower`, `replace('_', ' ')`, `string`, `tojson` e o filtro próprio `numero` (`22.0` → `22`) |
| Funções globais | `url_for(...)`, `csrf_token()`, `get_flashed_messages(with_categories=true)` |
| Objetos do Flask | `g.usuario`, `g.casa_id`, `g.nome_casa`, `session`, `request` |

O filtro `numero` é registrado em `criar_app()` com a função `formatar_numero()` de `models/rotina.py`; `csrf_token()` vem de um `context_processor` no mesmo arquivo.

### 2.3 Componentes visuais reutilizados

Não há *macros* Jinja; a reutilização acontece por meio de classes CSS comuns a várias telas:

| Classe | Uso |
| --- | --- |
| `cartao` | Caixas brancas com borda e cantos arredondados (estatísticas, cômodos, dispositivos, rotinas, formulários) |
| `cabecalho-pagina` e `sobretitulo` | Título de cada página, com um rótulo em maiúsculas acima |
| `botao primario`, `botao secundario`, `botao discreto`, `link-perigo` | Ações principais, secundárias, pequenas e destrutivas |
| `status` e `status ativo` | Etiquetas "Ligado/Desligado" e "Ativa/Pausada" |
| `formulario`, `formulario-em-linha` | Formulários em coluna ou em linha |
| `cartao vazio`, `texto-vazio` | Mensagens de lista vazia |

## 3. Telas do sistema

<!--
Capturas reais podem ser adicionadas futuramente em assets/capturas/
(por exemplo painel.png, dispositivos.png, rotinas.png, historico.png,
login.png, cadastro.png e casa.png) e referenciadas nesta seção.
-->

### 3.1 Login — `entrar.html`

- **Finalidade:** acessar a conta.
- **Rota:** `GET` e `POST` `/entrar`.
- **Conteúdo:** a ilustração `sala-habitus.png`, o título "Bem-vindo de volta", os campos de e-mail e senha e o link "Criar conta".
- **Interações:** o botão de olho alterna a visibilidade da senha (seção 5.2); o envio mostra "E-mail ou senha incorretos." em caso de erro.
- **Perfis:** não se aplica. Quem já está logado é redirecionado ao painel.

### 3.2 Cadastro — `cadastro.html`

- **Finalidade:** criar a conta e a casa; quem se cadastra se torna administrador.
- **Rota:** `GET` e `POST` `/cadastro`.
- **Campos:** nome, e-mail, nome da casa, **cômodos iniciais** e senha com confirmação.
  - Os cômodos iniciais são escolhidos por botões de opção: "Usar sugeridos", o padrão, ou "Começar sem cômodos".
  - Um botão ⓘ explica as duas opções num balão, mostrado por CSS ao passar o mouse ou focar o botão.
- **Interações:** ver ou ocultar a senha; após o cadastro, o painel exibe o pop-up "Conta criada" (seção 5.3).

### 3.3 Troca obrigatória de senha — `trocar_senha.html`

- **Finalidade:** trocar a senha temporária no primeiro acesso.
- **Rota:** `GET` e `POST` `/trocar-senha`.
- **Conteúdo:** o título "Crie sua senha", uma saudação com o nome da pessoa, os campos de nova senha e confirmação e o botão "Sair".
- **Particularidade:** a tela usa a estrutura `sem-sistema`, sem o menu, porque as demais páginas ficam bloqueadas até a troca.

### 3.4 Painel — `painel.html`

- **Finalidade:** visão geral da casa aberta.
- **Rota:** `GET /painel`.
- **Conteúdo:**
  - o título "Minha casa" e o botão "Gerenciar dispositivos";
  - quatro indicadores: dispositivos ativos, ligados agora, cômodos e rotinas ativas;
  - um cartão por cômodo, com seus aparelhos e o estado de cada um;
  - "Atividade recente": as 6 últimas alterações, com dispositivo, ação, responsável ("Automação" para rotinas) e `dd/mm HH:MM`.
- **Perfis:** a tela é igual para administrador e comum.

### 3.5 Minha casa — `casa.html`

- **Finalidade:** cômodos, moradores e troca de casa.
- **Rotas:**
  - `GET /casa`;
  - `POST /casa/selecionar`;
  - `POST /casa/comodos`, `.../renomear` e `.../remover`;
  - `POST /casa/moradores`, `.../perfil` e `.../remover`.

| Elemento | Todos os membros | Somente administrador |
| --- | --- | --- |
| Cabeçalho com o nome da casa e o perfil | ✅ | — |
| "Trocar de casa" (só se a pessoa participa de mais de uma) | ✅ | — |
| Lista de cômodos, com a quantidade de dispositivos ativos | ✅ | Campo para renomear; "Excluir" só para cômodos sem nenhum dispositivo ligado (`total_dispositivos == 0`); com ativos, dica para transferi-los em Dispositivos; só com removidos, a dica "Guarda o histórico de dispositivos removidos." |
| Formulário "Novo cômodo" | — | ✅ |
| Lista de moradores (nome, perfil e e-mail) | ✅ | Seletor de perfil e "Remover" para os outros moradores |
| Senha temporária recém-gerada (`role="alert"`, texto selecionável com um clique) | — | ✅, só na resposta ao cadastro |
| Formulário "Adicionar morador" (e-mail, nome opcional, permissão) | — | ✅ |

### 3.6 Dispositivos — `dispositivos.html`

- **Finalidade:** ver e controlar os aparelhos.
- **Rotas:** `GET` e `POST` `/dispositivos`; `POST /dispositivos/<id>/controle`, `/transferir` e `/remover`.
- **Cartão de cada aparelho:**
  - ícone do tipo (☼ luz, ❄ ar-condicionado, ♨ aquecedor, ✳ ventilador, ⌁ outro);
  - etiqueta "Ligado/Desligado";
  - nome, cômodo e tipo;
  - botão Ligar/Desligar.

| Elemento | Todos os membros | Somente administrador |
| --- | --- | --- |
| Botão Ligar/Desligar (AJAX) | ✅ | — |
| Controle deslizante de brilho, temperatura ou intensidade, com "Salvar …" (AJAX) | ✅, para os tipos com ajuste | — |
| Formulário "Adicionar dispositivo" (nome, tipo, cômodo) | — | ✅, desativado se não houver cômodos |
| "Mover para" (outro cômodo) | — | ✅, só com mais de um cômodo |
| "Remover dispositivo", com confirmação | — | ✅ |

Os limites, o passo e a unidade de cada controle deslizante vêm do atributo `ajuste` das classes Python. Por exemplo, a temperatura usa `min="16" max="30" step="0.5"`.

### 3.7 Rotinas — `rotinas.html`

- **Finalidade:** programar ações por horário.
- **Rotas:** `GET` e `POST` `/rotinas`; `GET` e `POST` `/rotinas/<id>/editar`; `POST /rotinas/<id>/alternar` e `/remover`.
- **Formulário** (somente administrador):
  - nome, dispositivo, ação, valor (controle deslizante), horário (`type="time"`) e dias da semana (Seg a Dom);
  - na edição, o cartão do formulário e o da rotina ficam destacados, e aparece "Cancelar edição".
- **Lista** (todos): cada rotina mostra o estado (Ativa/Pausada), o nome, o dispositivo e o cômodo, o horário, a ação ("Ajustar brilho para 75%") e os dias ("Segunda a sexta").
- **Ações por rotina** (somente administrador): "Editar", "Pausar"/"Ativar" e "Excluir", com confirmação.

### 3.8 Histórico — `historico.html`

- **Finalidade:** consultar as 100 alterações mais recentes.
- **Rota:** `GET /historico`.
- **Conteúdo:** tabela com data e hora (`dd/mm/aaaa HH:MM`), dispositivo, cômodo, ação, "antes → depois" e responsável ("Automação" quando não há usuário). Os valores aparecem como foram gravados (por exemplo, `0 → 1` ao ligar); valores ausentes viram "—". A tabela rola na horizontal em telas estreitas.
- **Perfis:** a tela é igual para todos.

## 4. CSS e responsividade

### 4.1 Organização de `estilo.css`

O arquivo é dividido por comentários:

| Linhas | Seção |
| --- | --- |
| 1–26 | Variáveis (`:root`) e estilos gerais |
| 28–52 | Menu lateral |
| 54–101 | Páginas do sistema: barra superior, cartões, botões, estatísticas, ambientes, eventos |
| 103–125 | Formulários e cartões de dispositivos |
| 127–140 | Rotinas |
| 142–198 | Casa, moradores e histórico |
| 200–216 | Login e cadastro (versão inicial) |
| 218–241 | Pontos de quebra 1150px e 760px |
| 243–318 | Tipografia e telas de acesso inspiradas no layout do Figma (classes com sufixo `-figma`) |
| 319–326 | Pop-up de conta criada |
| 328–340 | Pontos de quebra 900px e 520px |
| 342–350 | Formulário de rotina: controle deslizante e edição |

As regras foram acrescentadas por etapas. Por isso, algumas aparecem duas vezes: `.sem-sistema` é definida na linha 201 e sobrescrita por `body.sem-sistema` na linha 248, que vale por ser mais específica.

### 4.2 Variáveis, cores e tipografia

As variáveis de `:root`:

| Variável | Valor | Usos |
| --- | --- | :---: |
| `--fundo` | `#f3f6fa` | 1 |
| `--texto` | `#17283e` | 1 |
| `--muted` | `#708096` | 2 |
| `--borda` | `#e2e9f1` | 3 |
| `--azul` | `#2563eb` | 7 |
| `--verde` | `#119d75` | **0** (definida, sem uso) |
| `--lateral` | `#111d30` | 1 |
| `--cartao` | `#fff` | 1 |
| `--raio` | `15px` | 1 |

Muitas cores aparecem diretamente nas regras, sem variável. Alguns exemplos:

| Cor | Onde aparece |
| --- | --- |
| `#54bfd4` | Borda ciano dos cartões |
| `#275bd1` | Item selecionado do menu |
| `#00a9c1` | Números das estatísticas e horário das rotinas |
| `#a93b49` | Avisos de erro |
| `#107b58` | Avisos de sucesso |

**Tipografia:**

- a regra inicial do `body` usa `system-ui` com 15px e altura de linha 1.5;
- mais adiante, `body { font-family: Montserrat, Arial, sans-serif; }` substitui a família;
- a linha 244 tenta importar a Montserrat do Google Fonts, mas, por estar depois de outras regras, esse `@import` deve ser ignorado pelos navegadores, conforme a especificação CSS. Na prática, a fonte será a Montserrat se estiver instalada no computador, ou a Arial;
- os títulos usam `clamp(27px, 3vw, 37px)` no `h1`.

### 4.3 Layout, cartões e formulários

| Elemento | Regra |
| --- | --- |
| Menu lateral | `position: fixed`, 245px de largura, fundo `--lateral`; a área principal tem `margin-left: 245px` |
| Conteúdo | Largura máxima de 1430px, com 35px de espaçamento interno |
| Estatísticas do painel | Grade de 4 colunas |
| Cômodos, dispositivos e rotinas | Grades de 3 colunas |
| Minha casa | Duas áreas (`1fr 1.4fr`): cômodos e moradores |
| Formulário em linha | 4 colunas (ex.: nome, tipo, cômodo e botão) |
| Telas de acesso | Cartão de até 1120px com duas colunas: imagem (47%) e formulário (53%) |
| Cartões | Fundo branco, borda de 1.5px `#54bfd4`, cantos de `--raio` |
| Campos | Altura mínima de 42px, borda `#d9e3ef`, contorno azul ao focar |

### 4.4 Pontos de quebra

| Largura máxima | Mudanças |
| --- | --- |
| **1150px** | Estatísticas e grades passam a 2 colunas; Minha casa fica numa coluna; formulário em linha com 2 colunas |
| **900px** | Telas de acesso numa coluna, com a imagem reduzida a 214px de altura |
| **760px** | O menu lateral sai da tela e passa a abrir pelo botão ☰; a área principal ocupa toda a largura; grades e formulários numa coluna; a descrição da barra superior é ocultada |
| **520px** | No cabeçalho das telas de acesso, os itens quebram de linha, e a marca diminui para 32px |

### 4.5 Menu lateral em telas menores

Abaixo de 760px, o menu recebe `transform: translateX(-100%)`, ficando fora da tela. O botão `#abrir-menu` (☰), visível só nessa faixa, alterna a classe `aberto`, que traz o menu de volta (`translateX(0)`) com uma transição de 0,2s. Não há botão separado para fechar: o mesmo ☰ fecha o menu, e navegar para outra página também o fecha, porque a página é recarregada.

## 5. JavaScript

`frontend/static/js/app.js` tem sete blocos independentes. Cada um procura seus elementos na página e só age se eles existirem. O comentário inicial resume a proposta: "As regras continuam no Python".

### 5.1 Resumo

| Bloco | Seletor | O que faz |
| --- | --- | --- |
| Mostrar senha | `.mostrar-senha-figma` | Alterna o campo anterior entre `password` e `text`; atualiza `aria-label` e a classe `ativo` (que mostra o risco no ícone de olho) |
| Pop-up de conta criada | `.aviso` com o texto "Conta criada!" | Cria um diálogo (`role="dialog"`, `aria-modal="true"`) com o botão "Continuar", que o remove |
| Controles deslizantes | `input[type="range"]` | Atualiza o texto `[data-valor]` do mesmo rótulo com o valor e a unidade (`data-unidade`) |
| Confirmações | `form[data-confirmar]` | Pede confirmação com `window.confirm()` antes de enviar; cancela o envio se a pessoa recusar |
| Envio por AJAX | `form[data-ajax]` | Envia o formulário com `fetch()` e recarrega a página (seção 6) |
| Menu | `#abrir-menu` | Alterna a classe `aberto` em `#menu-lateral` |
| Formulário de rotinas | `#tipo-dispositivo`, `#acao-rotina`, `#valor-rotina` | Mostra só as ações compatíveis e ajusta o controle de valor (seção 5.4) |

### 5.2 Confirmações e alertas

Usam os diálogos nativos do navegador:

| Diálogo | Quando aparece |
| --- | --- |
| `window.confirm()` | Excluir cômodo; remover morador; remover dispositivo; excluir rotina (atributo `data-confirmar` de cada formulário) |
| `window.alert()` | Erro num controle via AJAX |

### 5.3 Pop-up "Conta criada"

Depois do cadastro, a rota mostra a mensagem `flash` "Conta criada! …" no painel. O script procura um `.aviso` com esse texto e cria o pop-up. O conteúdo do pop-up é fixo, sem dados digitados pelo usuário. A ligação entre os dois depende do texto exato da mensagem: se ela mudar no Python, o pop-up deixa de aparecer.

### 5.4 Formulário de rotinas

O formulário recebe os limites dos ajustes do servidor, em JSON, no atributo `data-ajustes` (gerado com `{{ ajustes|tojson }}`). Cada opção de dispositivo traz as ações que a sua classe aceita em `data-acoes` (por exemplo, `"ajustar_brilho desligar ligar"` para uma luz, em ordem alfabética).

A função `ajustarOpcoes()`, chamada ao carregar a página e ao mudar o dispositivo ou a ação:

1. esconde e desativa as ações que o dispositivo não aceita; se a ação escolhida ficar inválida, volta para "Ligar";
2. mostra o campo de valor só para ações `ajustar_*`; nas demais, o campo fica **desativado**, e um campo desativado não é enviado;
3. ajusta `min`, `max`, `step` e a unidade conforme o ajuste;
4. define o valor inicial: o valor salvo, na edição e enquanto a ação original estiver escolhida, ou o meio da faixa (50% ou 23 °C).

O servidor valida tudo de novo; o script só evita escolhas inválidas na tela.

## 6. Comunicação com o back-end: controle de um dispositivo

Exemplo: ajustar o brilho da "Luz da sala" (dispositivo 5) para 45%.

**1. O HTML gerado pelo servidor** (`dispositivos.html`):

```html
<form class="form-controle controle-nivel" data-ajax method="post" action="/dispositivos/5/controle">
    <input type="hidden" name="csrf_token" value="…token da sessão…">
    <input type="hidden" name="acao" value="ajustar_brilho">
    <label>Brilho <strong data-valor>80%</strong>
        <input type="range" name="valor" min="0" max="100" step="1" value="80" data-unidade="%">
    </label>
    <button class="botao discreto" type="submit">Salvar brilho</button>
</form>
```

**2. O envio** (`app.js`):

```javascript
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
```

**3. O caminho completo:**

| Etapa | Onde | O que acontece |
| :---: | --- | --- |
| 1 | Navegador | Ao arrastar o controle, o texto muda para "45%" (só na tela) |
| 2 | `app.js` | "Salvar brilho" envia o `FormData` (`csrf_token`, `acao`, `valor=45`) com o cabeçalho `X-Requested-With`; o botão é desativado |
| 3 | Flask | Confere a sessão, o perfil e o token CSRF ([ROTAS_E_PERMISSOES.md](ROTAS_E_PERMISSOES.md#44-como-o-vínculo-com-a-casa-é-verificado)) |
| 4 | Serviço e modelo | `Luz.executar("ajustar_brilho", "45")` valida; o banco recebe o `UPDATE` e o registro de histórico |
| 5 | Rota | Responde `{"ok": true, "resultado": {"campo": "brilho", "antes": 80, "depois": 45}}` |
| 6 | `app.js` | Recarrega a página, que é gerada de novo com os dados do banco |

- **Atualização da tela:** o JavaScript **não atualiza partes da página** com os dados da resposta; ele a recarrega por inteiro. A tela sempre reflete o estado gravado, ao custo de uma nova requisição.
- **Em caso de erro**, por exemplo um valor fora da faixa, a resposta é `400` com `{"erro": "..."}`; o script mostra a mensagem num alerta e reativa o botão.
- **Formato completo** das respostas JSON: [ROTAS_E_PERMISSOES.md](ROTAS_E_PERMISSOES.md#63-controle-de-dispositivos-em-json).

## 7. Segurança na interface

| Cuidado | Como é aplicado | Observação |
| --- | --- | --- |
| Escape automático | O Jinja escapa as variáveis dos templates `.html`; o projeto não usa o filtro `safe` | Um nome como `<b>Sala</b>` aparece como texto |
| Dados para o JavaScript | Os limites dos ajustes vão em `data-ajustes` pelo filtro `tojson`, que produz JSON seguro dentro do HTML | Os dados vêm das classes, não do usuário |
| Pop-up de conta | O `innerHTML` do pop-up é um texto fixo, sem dados do usuário | — |
| CSRF | Todos os formulários POST têm o campo oculto `csrf_token`; o AJAX o envia dentro do `FormData` | Detalhes em [AUTENTICACAO_E_SEGURANCA.md](AUTENTICACAO_E_SEGURANCA.md#81-proteção-csrf) |
| Elementos por perfil | `{% if g.usuario.pode_gerenciar() %}` esconde formulários e botões de gestão do perfil `comum` | Apenas visual (veja abaixo) |
| Senha temporária | Exibida só na resposta do cadastro, com `Cache-Control: no-store` | Definido pela rota, não pelo template |

**Esconder um botão não é autorização.** Um usuário pode enviar um POST manualmente, por exemplo com as ferramentas do navegador, mesmo sem ver o botão. Quem impede a ação é o servidor: `@administrador_obrigatorio` responde 403, e os serviços só operam sobre registros da casa aberta. O template apenas evita mostrar opções que o servidor recusaria.

## 8. Implementação, planejamento visual e Figma

| Material | O que é | Situação |
| --- | --- | --- |
| `frontend/` | O front-end **implementado**, descrito neste documento | Conferido no código em 08/11/2026 |
| [TELAS_FIGMA.md](TELAS_FIGMA.md) | Guia de **planejamento visual** para desenhar as telas no Figma | Desatualizado em relação ao código: não cita a opção de cômodos iniciais nem a tela de troca de senha |
| Protótipo no Figma | Arquivo externo ao repositório | **Não conferido.** Não é possível afirmar se corresponde ao sistema |

As telas de login e cadastro usam classes com o sufixo `-figma`, e o CSS tem o comentário "inspirada no layout do Figma". Isso indica a intenção de seguir o protótipo, **não** que as telas sejam idênticas a ele. A comparação precisa ser feita à parte.

## 9. Limitações e pontos a testar no navegador

**Limitações confirmadas no código:**

- **Erros de AJAX pouco claros.** Se a sessão expirar ou o token CSRF for recusado, o servidor responde em HTML. O `app.js` falha ao ler o JSON e mostra no alerta o erro técnico da leitura, em vez da mensagem "Sessao expirada".
- **Recarga completa** após cada controle (seção 6).
- **Fonte externa provavelmente não carregada:** o `@import` do Google Fonts está fora do início do CSS.
- **CSS sem uso:**
  - a variável `--verde` não é usada;
  - as regras de `.opcoes-comodos`, sem o sufixo `-figma`, não são usadas por nenhum template;
  - parte das regras de "Login e cadastro" (linhas 200–216) é sobrescrita pelas telas de acesso posteriores.
- **Dependência de texto:** o pop-up "Conta criada" depende do texto exato da mensagem `flash`.
- **Diálogos nativos:** `confirm()` e `alert()` bloqueiam a página e não seguem o visual do sistema.
- **Sem testes automatizados** de JavaScript ou de interface.

**A verificar manualmente no navegador:**

- **Largura da tela de troca de senha:** `.acesso { max-width: 430px }` é sobrescrita por `body.sem-sistema .acesso { max-width: 1120px }`, então o cartão `cartao-acesso` pode ficar mais largo que o previsto.
- **Ações escondidas no formulário de rotinas:** a eficácia de `hidden` em elementos `<option>` varia entre navegadores. Como as opções também ficam `disabled`, elas não podem ser escolhidas mesmo quando aparecem.
- **Responsividade** nos quatro pontos de quebra e o menu ☰ abaixo de 760px.
- **Fonte efetivamente usada** (Montserrat ou Arial).
- **Recursos de acessibilidade:** o pop-up com `role="dialog"`, a senha temporária com `role="alert"`, os `aria-label` dos botões e o contorno de foco (`:focus-visible`).
- **Interações em geral:** ver ou ocultar a senha, as confirmações, os alertas de erro e o formulário de rotinas na criação e na edição.

## 10. Estado da verificação e fontes

Conferido com o código em 08/11/2026.

**Testado** (testes isolados executados em 08/11/2026, 19:05: `141 passed`):

- telas de login e cadastro renderizadas: `test_tela_de_login`, `test_tela_de_cadastro`;
- opções de cômodos iniciais no cadastro: `test_tela_de_cadastro_oferece_as_opcoes_de_comodos`;
- painel com dispositivos por cômodo e "Automação": `test_painel_agrupa_dispositivos_por_comodo`;
- limites das classes, filtro `numero`, "Salvar brilho" e "Mover para" na página de dispositivos: `test_pagina_de_dispositivos_usa_limites_das_classes`;
- lista de rotinas sem o botão "Editar" para o perfil comum: `test_lista_mostra_os_dados_salvos_depois_de_atualizar`;
- formulário de edição preenchido, com `data-salvo`, ação selecionada e dias marcados: `test_editar_abre_formulario_preenchido`;
- tela de troca de senha durante a troca obrigatória: `test_sem_trocar_a_senha_nao_acessa_outras_paginas`;
- senha temporária exibida uma vez: `test_administrador_ve_a_senha_temporaria_uma_unica_vez`.

**Verificado só na leitura do código:**

- os oito templates e o `base.html`;
- as diferenças por perfil nas tabelas da seção 3;
- todas as regras e pontos de quebra do CSS, incluindo as contagens de uso das variáveis, obtidas com busca no arquivo;
- os sete blocos de `app.js`.

**Não verificado:** a renderização no navegador e a comparação com o protótipo do Figma.

**Fontes:** `frontend/templates/base.html`, `entrar.html`, `cadastro.html`, `trocar_senha.html`, `painel.html`, `casa.html`, `dispositivos.html`, `rotinas.html`, `historico.html`, `frontend/static/css/estilo.css`, `frontend/static/js/app.js`, `backend/app/__init__.py`, `backend/app/routes/` (para as variáveis enviadas aos templates), `backend/app/services/dispositivos.py`, `backend/app/services/rotinas.py`, `backend/app/models/dispositivo.py`, `backend/app/models/rotina.py`, `docs/TELAS_FIGMA.md`, `tests/test_paginas.py`, `tests/test_comodos.py`, `tests/test_rotinas.py`, `tests/test_moradores.py`.
