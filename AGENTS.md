# AGENTS.md — Habitus Smart Home 2050

## Finalidade deste arquivo

Estas instruções orientam agentes de IA que forem **analisar, documentar, testar ou, quando expressamente autorizado, modificar** o projeto Habitus Smart Home 2050. O objetivo é preservar o funcionamento existente e impedir descrições ou alterações baseadas em suposições.

**Regra principal:** antes de responder sobre uma funcionalidade, examine o código correspondente. Documentação (inclusive este arquivo, o `README.md` e `docs/`) não é prova de implementação. Se não conseguir verificar, informe a limitação.

Todo o conteúdo das seções 1 a 12 foi conferido na leitura do código em 08/11/2026; os resultados de testes das seções 11 e 13 foram atualizados em 09/11/2026. A seção 13 separa o que tem teste automatizado do que foi verificado apenas lendo o código e do que depende do ambiente.

## 1. Contexto e escopo

- Projeto acadêmico da ExpoTech 2026.2, de Ciência da Computação.
- Aplicação web **local** que simula o gerenciamento de uma casa inteligente. O estado dos aparelhos é salvo no MySQL; não há controle de equipamentos físicos nem integração com Alexa, Google Home ou IoT.
- Idioma da interface e das mensagens: **português brasileiro**. Grande parte dos textos no código Python está sem acentos (ex.: "Comodo nao encontrado"); preserve os textos existentes ao citá-los.
- A pasta `Habitus/` é a **raiz do projeto** (antes chamada `Habitus_Smart_Home_2050_V2/`; renomeada em 09/11/2026). Todos os caminhos abaixo são relativos a ela. Na data da análise, ela **não** é um repositório git (não há `.git`).

## 2. Tecnologias e dependências

| Camada | Tecnologia | Observação |
| --- | --- | --- |
| Back-end | Python 3, Flask | `.venv` existente usa Python 3.14.6 |
| Banco | MySQL **8.0.16 ou superior** | Exigido pelos `CHECK` do `schema.sql` |
| Acesso ao banco | PyMySQL | `DictCursor`, `autocommit=False`, `utf8mb4` |
| Configuração | python-dotenv | Lê o `.env` |
| Senhas | `werkzeug.security` (`generate_password_hash` / `check_password_hash`) | **Não** há bcrypt |
| Templates | Jinja2 (via Flask) | HTML renderizado no servidor |
| Front-end | HTML, CSS e JavaScript puro | Sem framework, sem npm, sem etapa de build |
| Testes | pytest | Configurado em `pytest.ini` |

- `backend/requirements.txt` lista apenas Flask, PyMySQL, python-dotenv e pytest. **Werkzeug e Jinja2 não estão listados**: são instalados como dependências do Flask, embora o código importe `werkzeug.security` diretamente.
- O CSS contém um `@import` do Google Fonts (Montserrat) **no meio do arquivo** (`frontend/static/css/estilo.css`, após outras regras). Pela especificação CSS, um `@import` fora do início é ignorado; o carregamento real da fonte não foi verificado em navegador. Não descreva o projeto como "100% offline" nem como dependente do Google Fonts sem testar.

## 3. Estrutura do projeto

```text
backend/
  run.py                    # Cria o app e executa app.run(debug=True)
  executar_rotinas.py       # Executor de rotinas (segundo processo, laço de 20 s)
  requirements.txt
  .env.example              # Modelo de configuração, sem segredos reais
  app/
    __init__.py             # criar_app(): blueprints, before_request, CSRF, erros 400/403/404, filtro |numero
    config.py               # Caminhos e leitura do .env
    database.py             # conectar() e transacao()
    permissoes.py           # @login_obrigatorio e @administrador_obrigatorio
    models/                 # dispositivo.py, usuario.py, comodo.py, rotina.py
    validators/             # campos.py (genéricas), usuarios.py, casas.py, dispositivos.py, rotinas.py
    repositories/           # SQL parametrizado, um arquivo por tabela
    services/               # autenticacao, casas, comodos, dispositivos, moradores, rotinas
    routes/                 # autenticacao (auth), site, casas, dispositivos, rotinas, historico
    structures/             # fila_rotinas.py: FilaRotinas (heapq + deque)
frontend/
  templates/                # base, entrar, cadastro, trocar_senha, painel, dispositivos, rotinas, historico, casa
  static/css/estilo.css
  static/js/app.js
  static/img/sala-habitus.png
database/
  schema.sql                # Cria o banco do zero
  migracao_se_ja_criou_banco.sql, migracao_comodos.sql, migracao_moradores.sql
tests/                      # pytest; apoio_banco.py contém o banco falso
docs/                       # Documentação técnica; índice em docs/README.md (seção 16)
pytest.ini
README.md
.gitignore                  # Ignora .env, .venv/, __pycache__/, *.pyc, .pytest_cache/, .idea/, .vscode/, .DS_Store
```

Também existem, na raiz, um `.venv/` e um `.env` locais. Não leia nem exiba os valores do `.env`.

## 4. Arquitetura

### 4.1 Camadas

| Camada | Responsabilidade | Regra a preservar |
| --- | --- | --- |
| `routes/` | Recebe o pedido, aplica a permissão, chama o serviço, devolve template, redirecionamento ou JSON | Não contém SQL |
| `services/` | Regras de negócio; decide o que entra em cada transação | Sempre recebe o `id_casa` da casa aberta |
| `validators/` | Limpa e valida entradas; levanta `ValueError` com mensagem exibível | — |
| `models/` | Comportamento dos dispositivos e formatação de usuários, cômodos e rotinas | Limites dos ajustes ficam no atributo `ajuste` de cada classe |
| `repositories/` | SQL com parâmetros `%s`; recebem o cursor como primeiro argumento | Não contêm regra de negócio |
| `structures/` | `FilaRotinas` para o executor | — |
| `database.py` | `transacao()`: commit no sucesso, rollback em exceção, fecha a conexão sempre | Operações relacionadas ficam na mesma transação |

Os serviços tratam `ValueError` como erro de negócio; as rotas o transformam em mensagem `flash` (ou JSON, no controle via AJAX).

### 4.2 Ciclo de uma requisição

1. `before_request` em `app/__init__.py`, nesta ordem:
   - `carregar_usuario`: se há `usuario_id` na sessão, chama `services/autenticacao.carregar_acesso()` (**uma consulta ao MySQL em toda requisição autenticada**) e preenche `g.usuario`, `g.casa_id` e `g.nome_casa`. Se o usuário não participa de nenhuma casa, a sessão é limpa.
   - `exigir_troca_de_senha`: com `trocar_senha` na sessão, só são liberados `auth.trocar_senha`, `auth.sair` e `static`.
   - `proteger_formularios`: POST/PUT/PATCH/DELETE exigem token CSRF igual ao da sessão; sem ele, erro 400.
2. Rota → serviço → validadores/modelos → repositórios → MySQL.
3. Resposta: template HTML, redirecionamento com `flash`, ou JSON (somente em `/dispositivos/<id>/controle` com o cabeçalho `X-Requested-With: XMLHttpRequest`).
4. Erros 400, 403 e 404 usam um manipulador único que devolve um HTML simples.

### 4.3 Classes

| Classe | Arquivo | Papel |
| --- | --- | --- |
| `Dispositivo` → `Luz`, `Climatizador` (→ `ArCondicionado`, `Aquecedor`), `Ventilador`, `Generico` | `models/dispositivo.py` | Estado encapsulado, herança de ligar/desligar e `executar(acao, valor)` polimórfico, que devolve `(coluna, valor anterior, valor novo)` |
| `Usuario` | `models/usuario.py` | Perfil na casa aberta; `pode_gerenciar()` e `pode_controlar_dispositivo()` |
| `Comodo` | `models/comodo.py` | Valida o nome e compara sem diferenciar maiúsculas e espaços |
| `Rotina` | `models/rotina.py` | Converte a linha do banco em textos da tela (horário, dias, ação, valor) |
| `FilaRotinas` | `structures/fila_rotinas.py` | Heap por próximo horário e `deque` FIFO de comandos vencidos |

Dicionários de apoio em `models/dispositivo.py`: `CLASSES` (tipo → classe), `TIPOS` (tipo → rótulo) e `AJUSTES` (ação → limites), reaproveitados por validação, telas e JavaScript.

## 5. Perfis e rotas

Os perfis são valores de `moradores.perfil`: **`administrador`** e **`comum`** (não `ADMIN`/`MORADOR`). O perfil é **por casa**: a mesma pessoa pode ser administradora de uma casa e comum em outra.

| Método | Rota | Acesso | Função |
| --- | --- | --- | --- |
| GET | `/` | Público | Redireciona para o painel ou o login |
| GET, POST | `/entrar` | Público | Login |
| GET, POST | `/cadastro` | Público | Cria conta e casa |
| GET, POST | `/trocar-senha` | Logado com troca pendente | Troca obrigatória da senha temporária |
| POST | `/sair` | Qualquer | Limpa a sessão |
| GET | `/painel` | Logado | Resumo da casa |
| GET | `/casa` | Logado | Cômodos, moradores e troca de casa |
| POST | `/casa/selecionar` | Logado | Abre outra casa da qual participa |
| POST | `/casa/comodos` | Administrador | Cria cômodo |
| POST | `/casa/comodos/<id>/renomear` | Administrador | Renomeia cômodo |
| POST | `/casa/comodos/<id>/remover` | Administrador | Exclui cômodo |
| POST | `/casa/moradores` | Administrador | Adiciona morador |
| POST | `/casa/moradores/<id>/perfil` | Administrador | Muda o perfil |
| POST | `/casa/moradores/<id>/remover` | Administrador | Remove o acesso |
| GET | `/dispositivos` | Logado | Lista e controles |
| POST | `/dispositivos` | Administrador | Cadastra dispositivo |
| POST | `/dispositivos/<id>/controle` | Logado (ambos os perfis) | Liga, desliga ou ajusta; JSON se for AJAX |
| POST | `/dispositivos/<id>/transferir` | Administrador | Muda de cômodo |
| POST | `/dispositivos/<id>/remover` | Administrador | Desativa |
| GET | `/rotinas` | Logado | Lista rotinas |
| POST | `/rotinas` | Administrador | Cria rotina |
| GET, POST | `/rotinas/<id>/editar` | Administrador | Edita rotina |
| POST | `/rotinas/<id>/alternar` | Administrador | Pausa ou ativa |
| POST | `/rotinas/<id>/remover` | Administrador | Exclui rotina |
| GET | `/historico` | Logado | Últimas 100 alterações |

Sem login, as rotas protegidas redirecionam para `/entrar`; um perfil `comum` em rota de administrador recebe 403. Os templates escondem os controles de gestão do perfil `comum`, mas a proteção real está nos decoradores.

## 6. Regras de negócio

### 6.1 Conta, login e sessão

- O cadastro cria, **numa única transação**, usuário, casa, vínculo `administrador` e cômodos iniciais. E-mail duplicado → "Esse e-mail ja esta cadastrado.".
- Opção de cômodos iniciais: `sugeridos` (padrão) cria Sala, Quarto e Cozinha, mais os dispositivos "Luz da sala" (luz) e "Ar do quarto" (ar-condicionado); `vazio` não cria nada.
- O e-mail é normalizado para minúsculas no cadastro e no login.
- O login faz `session.clear()` antes de gravar `usuario_id`. Se `usuarios.trocar_senha` = 1, grava `trocar_senha` na sessão e redireciona para `/trocar-senha`.
- A nova senha precisa ter 8 ou mais caracteres, ser confirmada e ser diferente da temporária. Ao salvar, `trocar_senha` volta a 0.
- Não há troca voluntária de senha, recuperação de senha, exclusão de conta nem tempo de expiração de sessão configurado.

### 6.2 Casas

- Uma pessoa pode participar de várias casas. A casa aberta fica em `session["casa_id"]`; se ela deixar de participar dessa casa, o sistema abre a primeira casa em que participa (`ORDER BY id_morador`).
- O seletor "Trocar de casa" só aparece com mais de uma casa.
- **Não existe tela para criar outra casa, renomear ou excluir uma casa**. Casas só nascem no cadastro; uma pessoa ganha acesso a outras sendo adicionada como moradora.
- Uma conta sem nenhum vínculo consegue autenticar, mas a sessão é limpa na requisição seguinte, sem mensagem.

### 6.3 Cômodos

- Nome de 2 a 80 caracteres, com espaços repetidos removidos. Não pode repetir nome na mesma casa, sem diferenciar maiúsculas (comparação em Python e índice `UNIQUE (id_casa, nome)`).
- A exclusão só é permitida quando **nenhum** dispositivo está ligado ao cômodo (`COUNT(*) = 0` em `dispositivos` para aquele `id_comodo`). É bloqueada se houver dispositivos **ativos** ("Transfira-os...") **ou** dispositivos **removidos** (`ativo = 0`), que continuam ligados ao cômodo porque guardam o histórico.
- A transferência muda o `id_comodo` do dispositivo, então ele deixa de contar para o cômodo de origem: depois de transferir todos os ativos, o cômodo pode ser excluído (se não houver removidos). Removidos não podem ser transferidos nem restaurados (`buscar_ativo` exige `ativo = 1`), então bloqueiam a exclusão de forma permanente pela interface. O `ON DELETE RESTRICT` garante a mesma regra no banco.

### 6.4 Dispositivos

| Tipo (`tipo`) | Classe | Ajuste | Faixa | Valor inicial |
| --- | --- | --- | --- | --- |
| `luz` | `Luz` | brilho | inteiro 0–100 % | 80 |
| `ar_condicionado` | `ArCondicionado` | temperatura | 16–30 °C, até 1 casa decimal | 22 |
| `aquecedor` | `Aquecedor` | temperatura | 16–30 °C, até 1 casa decimal | 25 |
| `ventilador` | `Ventilador` | intensidade | inteiro 0–100 % | 50 |
| `outro` | `Generico` | — (só liga/desliga) | — | — |

- Não há TV nem outros tipos específicos.
- A tela usa passo de 0,5 °C, mas o validador aceita qualquer valor com uma casa decimal (ex.: 22,3). Vírgula e ponto são aceitos.
- Cada controle (ligar, desligar, ajustar) faz, na mesma transação, `SELECT ... FOR UPDATE`, `UPDATE` da coluna e `INSERT` no histórico. Ajustar não liga o aparelho. Ligar um aparelho já ligado também gera histórico.
- Remover = `ativo = 0` (nunca `DELETE`) e **pausa todas as rotinas** do dispositivo. Dispositivos removidos e suas rotinas somem das listas; não há tela para restaurá-los.
- Transferir só aceita outro cômodo da mesma casa (não o atual) e grava `transferir_comodo` no histórico com os nomes dos cômodos. Configurações, rotinas e histórico continuam ligados ao mesmo `id_dispositivo`. A opção "Mover para" só aparece com mais de um cômodo.

### 6.5 Moradores

- Somente administradores adicionam moradores, mudam perfis e removem acessos.
- E-mail com conta existente: apenas cria o vínculo; o nome digitado é ignorado e a senha não muda. Se a pessoa já participa da casa, a operação é recusada.
- E-mail sem conta: o nome é obrigatório; é criada uma conta com senha temporária de 12 caracteres (sem `0`, `O`, `1`, `l`, `I`), gerada com `secrets`. Só o hash vai para o banco. A senha aparece **uma única vez** na resposta, com `Cache-Control: no-store`, e não fica na sessão. **O sistema não envia e-mails.**
- Remover morador apaga a linha em `moradores`; a conta continua existindo.
- Ninguém altera ou remove o próprio acesso; por isso o administrador que age continua sempre administrador.
- Todos os membros da casa (inclusive `comum`) veem nome, perfil e e-mail dos moradores em `/casa`.

### 6.6 Rotinas

- Campos: nome (2–100), dispositivo ativo da casa, ação, valor (só para `ajustar_*`), horário `HH:MM` e ao menos um dia.
- Ações: `ligar`, `desligar`, `ajustar_brilho`, `ajustar_temperatura`, `ajustar_intensidade`. O valor é validado executando a ação num objeto do dispositivo **em memória**: o cadastro não altera o aparelho nem o histórico.
- O formulário (JavaScript) mostra só as ações aceitas pela classe do dispositivo; o servidor valida de novo.
- `dias_semana` é salvo como `'todos'` ou como lista ordenada (`'0,2,4'`), com 0 = segunda e 6 = domingo.
- Editar mantém o mesmo `id_rotina`. Alternar inverte `ativa`. Excluir é `DELETE` real.

### 6.7 Painel e histórico

- O painel mostra: dispositivos ativos, quantos estão ligados, número de cômodos, rotinas ativas (de dispositivos ativos), dispositivos por cômodo e as 6 últimas alterações.
- `/historico` mostra as 100 alterações mais recentes da casa; o banco guarda todas.
- Alterações feitas por rotinas gravam `id_usuario = NULL` e ação `Rotina: <nome>`; a tela exibe "Automação" como responsável.
- O texto da ação é cortado em 60 caracteres e os valores em 50.

### 6.8 Validações

| Campo | Regra | Arquivo |
| --- | --- | --- |
| Nome da pessoa | 2–100 caracteres | `validators/usuarios.py` |
| E-mail | Minúsculas, até 150, formato `x@y.z` | `validators/usuarios.py` |
| Senha | 8+ caracteres e igual à confirmação | `validators/usuarios.py` |
| Perfil | `administrador` ou `comum` | `validators/usuarios.py` |
| Nome da casa | 2–100 caracteres | `validators/casas.py` |
| Nome do cômodo | 2–80 caracteres | `validators/casas.py` |
| Dispositivo | Nome 2–100, tipo em `CLASSES`, cômodo da casa | `validators/dispositivos.py` |
| Rotina | Ver 6.6 | `validators/rotinas.py` |
| Números | Rejeita texto, `nan` e `inf`; aceita vírgula | `validators/campos.py` |

Todos os textos têm espaços repetidos removidos antes da validação.

## 7. Executor de rotinas

- Roda em um **segundo processo**: `backend/executar_rotinas.py`. Sem ele, nenhuma rotina é executada.
- Laço: a cada 20 segundos, usa `datetime.now()` (horário local do computador), abre o contexto do app e chama `executar_pendentes(agora, ultima_verificacao)`. `ultima_verificacao` só avança quando a verificação termina sem exceção.
- Janela verificada (`services/rotinas.py`): `desde = max(ultima_verificacao ou agora − 1 min, agora − 10 min)`.
  - **Ao iniciar**, a janela é de apenas **1 minuto**.
  - Com o executor rodando, cobre todo o intervalo desde a última verificação bem-sucedida, até o teto de **10 minutos** (`ATRASO_MAXIMO`), por exemplo durante uma queda do MySQL.
  - Rotinas de períodos em que o executor estava **desligado não são recuperadas**.
- Fluxo: lista rotinas ativas de dispositivos ativos (todas as casas) → `FilaRotinas` calcula o próximo horário de cada uma depois de `desde` (heap com desempate por `id_rotina`, tratando a virada da meia-noite) → retira as vencidas até `agora` para um `deque` → executa cada uma em uma transação própria.
- Em cada execução: relê a rotina com `FOR UPDATE`; executa só se estiver ativa, o horário e o dia da semana conferirem e `ultima_execucao` for anterior ao horário agendado; relê o dispositivo ativo com bloqueio; aplica a ação; grava o histórico; atualiza `ultima_execucao` com o horário da verificação.
- Erros `ValueError` e `pymysql.MySQLError` de uma rotina viram mensagem no terminal e não impedem as próximas; outras exceções interrompem aquela verificação.

## 8. Banco de dados

### 8.1 Esquema (`database/schema.sql`)

- Cria o banco `habitus_smart_home` (`utf8mb4`, `utf8mb4_unicode_ci`). O nome está **fixo** no script, assim como nas migrações.
- Usa `CREATE TABLE IF NOT EXISTS`: executá-lo sobre um banco existente **não** atualiza tabelas antigas.

| Tabela | Colunas principais | Restrições |
| --- | --- | --- |
| `usuarios` | `id_usuario`, `nome`, `email`, `senha_hash`, `trocar_senha`, `criado_em` | `email` UNIQUE |
| `casas` | `id_casa`, `nome`, `endereco`, `criada_em` | `endereco` **não é usado** pelo código |
| `moradores` | `id_morador`, `id_casa`, `id_usuario`, `perfil` ENUM | UNIQUE (`id_casa`, `id_usuario`) |
| `comodos` | `id_comodo`, `id_casa`, `nome` | UNIQUE (`id_casa`, `nome`) |
| `dispositivos` | `id_dispositivo`, `id_comodo`, `nome`, `tipo` ENUM, `ligado`, `brilho`, `temperatura` DECIMAL(4,1), `intensidade`, `ativo` | CHECK de faixas: brilho e intensidade 0–100, temperatura 16–30 |
| `historico` | `id_historico`, `id_dispositivo`, `id_usuario` (anulável), `acao`, `valor_anterior`, `valor_novo`, `data_acao` | `data_acao` usa `CURRENT_TIMESTAMP` do MySQL |
| `rotinas` | `id_rotina`, `id_dispositivo`, `nome`, `acao` ENUM, `valor` DECIMAL(5,1), `horario` TIME, `dias_semana`, `ativa`, `ultima_execucao` | — |

### 8.2 Chaves estrangeiras (`ON DELETE`)

| Relação | Regra |
| --- | --- |
| `moradores` → `casas`, `usuarios` | CASCADE |
| `comodos` → `casas` | CASCADE |
| `dispositivos` → `comodos` | **RESTRICT** (`fk_dispositivos_comodo`) |
| `historico` → `dispositivos` | CASCADE |
| `historico` → `usuarios` | SET NULL |
| `rotinas` → `dispositivos` | CASCADE |

O app nunca apaga casas, usuários ou dispositivos, então essas cascatas não são acionadas pela interface.

### 8.3 Migrações (bancos criados por versões anteriores)

Executar somente com autorização, uma por vez, nesta ordem, e apenas as que ainda não foram aplicadas:

| Ordem | Arquivo | Efeito | Cuidados |
| --- | --- | --- | --- |
| 1 | `migracao_se_ja_criou_banco.sql` | Adiciona `rotinas.ultima_execucao` | Falha se a coluna já existir |
| 2 | `migracao_comodos.sql` | Troca a FK `dispositivos → comodos` de CASCADE para RESTRICT | Supõe o nome `dispositivos_ibfk_1`; o script mostra o nome real antes do `DROP` |
| 3 | `migracao_moradores.sql` | Adiciona `usuarios.trocar_senha` | Falha se a coluna já existir |

- Todas usam `USE habitus_smart_home`. Nenhuma apaga tabelas ou registros.
- Dependências no código: o executor exige `ultima_execucao`; cadastrar morador novo e trocar senha exigem `trocar_senha`. Login e cadastro de conta funcionam sem `trocar_senha`. Sem a migração 2, a exclusão de cômodo continua bloqueada pelo serviço, mas o banco não garante a regra.

### 8.4 Banco de testes `habitus_testes`

- Usado apenas por `tests/test_integracao_mysql.py`, que espera **exatamente** as 7 tabelas acima.
- **Nenhum script do projeto cria esse banco.** Ele precisa ser criado manualmente pelo usuário com a mesma estrutura do `schema.sql`. Não edite o `schema.sql` para isso; peça orientação ao usuário.

## 9. Configuração (`.env`)

- Variáveis lidas por `backend/app/config.py`: `SECRET_KEY`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`. Descreva-as a partir de `backend/.env.example`.
- Ordem de busca: `backend/.env`; se não existir, `.env` na raiz. Só o primeiro encontrado é carregado, e variáveis já definidas no ambiente do sistema têm prioridade.
- Padrões quando faltam: `DB_HOST` 127.0.0.1, `DB_PORT` 3306, `DB_USER` root, `DB_PASSWORD` vazio, `DB_NAME` habitus_smart_home e um `SECRET_KEY` fixo de teste (ver seção 11).
- Cookies de sessão: `HttpOnly` e `SameSite=Lax`.
- A última linha do `.env.example` é um comentário sobre fuso horário (`America/Sao_Paulo`) sem variável correspondente: o código não lê nenhuma configuração de fuso.

## 10. Execução local (Windows / PowerShell)

A partir da raiz do projeto, com Python e MySQL 8.0.16+ instalados:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

- Se a ativação for bloqueada: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
- Crie o `.env` a partir de `backend/.env.example` (seção 9) e o banco com `database/schema.sql` (ou as migrações, se o banco já existir).

Terminal 1 — site em `http://127.0.0.1:5000`:

```powershell
python backend\run.py
```

Terminal 2 — executor, com o mesmo ambiente virtual ativado:

```powershell
python backend\executar_rotinas.py
```

Dentro de `backend/`, use `python run.py` e `python executar_rotinas.py`. O `run.py` usa `debug=True` (depurador do Werkzeug): é apenas para desenvolvimento local.

Use o mesmo fuso horário no computador e no MySQL: o executor usa a hora local do Python, enquanto `historico.data_acao` usa a hora do servidor MySQL.

## 11. Testes

### 11.1 Organização

- `pytest.ini`: `pythonpath = backend tests` e `testpaths = tests`.
- `tests/apoio_banco.py`: `CursorFalso` registra os SQL e devolve respostas prontas; `usar_banco_falso()` substitui `transacao` nos módulos; `entrar_como()` cria um cliente logado (usuário 9, casa 7) com token CSRF de teste.

| Arquivo | Cobre | MySQL real? |
| --- | --- | --- |
| `test_modelos.py` | Classes de dispositivo, `Usuario`, dias e repetição de rotinas | Não |
| `test_estruturas.py` | `FilaRotinas`, heap, FIFO, atraso, meia-noite, dias | Não |
| `test_validadores.py` | Validadores | Não |
| `test_servicos.py` | `transacao()`, controle e cadastro de dispositivos, remoção, executor | Não |
| `test_comodos.py` | `Comodo`, CRUD de cômodos, transferência, permissões, cômodos iniciais | Não |
| `test_moradores.py` | Cadastro de morador, senha temporária, troca obrigatória | Não |
| `test_rotinas.py` | `Rotina`, salvar e editar, rotas e permissões | Não |
| `test_paginas.py` | Telas públicas, login obrigatório, CSRF, painel, fluxo de cadastro e login | Não |
| `test_integracao_mysql.py` | Conexão, 7 tabelas, CRUD de `usuarios`, FK e UNIQUE de `moradores` | **Sim** |

### 11.2 Testes isolados (sem MySQL)

```powershell
python -m pytest -v --ignore=tests/test_integracao_mysql.py
```

Resultado atual (09/11/2026; Python 3.14.6, pytest 9.2.0): os 141 isolados passaram dentro da suíte completa, `python -m pytest -v` → **`144 passed in 2.47s`** (141 isolados + 3 de integração). Histórico: em 08/11/2026 (com Flask 3.1.3, Werkzeug 3.1.9 e PyMySQL 1.2.3), só os isolados → `141 passed`. Aprovação não é cobertura: o projeto não mede cobertura de código; nunca afirme 100%. Para não gravar `.pytest_cache` nem `__pycache__` numa análise somente leitura, acrescente `-p no:cacheprovider` e use `python -B`.

### 11.3 Testes de integração (MySQL real)

```powershell
python -m pytest -v tests/test_integracao_mysql.py
```

Execute **somente com autorização e após conferir o ambiente**:

- São 3 testes. Eles escrevem no banco `habitus_testes` e desfazem tudo com `rollback`.
- Leem **apenas o `.env` da raiz** (não o `backend/.env`) e exigem `DB_USER` e `DB_PASSWORD` definidos (`KeyError` se faltarem). Usam as mesmas credenciais do banco principal, com o nome do banco fixo no código.
- Usam SQL direto: validam o esquema, **não** os `repositories` nem os `services`.
- Não são pulados sem MySQL: `python -m pytest -v` sem exclusões **falha** se o banco de testes não estiver disponível.
- Resultado atual: **executados e aprovados em 09/11/2026** no banco `habitus_testes` → `3 passed in 0.50s` (Python 3.14.6, pytest 9.2.0). Em 08/11/2026 não tinham sido executados. Antes de rodá-los de novo, a regra acima continua valendo.

Não existem testes de JavaScript, de interface no navegador nem de carga.

Ao alterar código com autorização: execute os testes relacionados, registre o comando e relate o que passou, falhou ou não pôde ser executado. Nunca invente resultados.

## 12. Segurança

### 12.1 Proteções existentes (preservar)

- Hash de senha com `werkzeug.security`; a senha temporária é exibida uma vez e não é armazenada em texto.
- CSRF: token aleatório na sessão, conferido com `hmac.compare_digest` em todo método que altera estado, inclusive login e cadastro. É aceito no campo `csrf_token` ou no cabeçalho `X-CSRF-Token`.
- `session.clear()` no login e no cadastro (evita fixação de sessão).
- Perfil e vínculo com a casa são relidos do banco a cada requisição: remoção ou mudança de perfil vale imediatamente.
- Isolamento por casa: listagens filtram por `id_casa`, e toda alteração iniciada pelo usuário primeiro busca o registro com o `id_casa` da casa aberta (alguns `UPDATE`/`DELETE` usam só o id, depois dessa busca). A exceção é o executor de rotinas, que trabalha com todas as casas.
- SQL parametrizado; a única coluna montada no texto (`atualizar_campo`) é conferida em `CAMPOS_CONTROLE`.
- Bloqueios `FOR UPDATE` e transações nas operações que leem e alteram.
- Jinja escapa automaticamente as variáveis dos templates `.html`; não introduza `|safe` com dados do usuário.

### 12.2 Limitações e cuidados

- Sem `.env`, o app inicia com um `SECRET_KEY` **fixo e público** e com usuário `root` sem senha. Nunca dependa desses padrões fora de testes.
- `debug=True` ativa o depurador interativo do Werkzeug: nunca exponha o servidor na rede.
- O manipulador de erros 400/403/404 insere `erro.description` no HTML **sem escape**. Hoje só recebe textos fixos; nunca passe entrada do usuário para `abort(description=...)`.
- Não há limite de tentativas de login, bloqueio de conta, cookie `Secure`, HTTPS, expiração de sessão configurada nem política de senha além de 8 caracteres.
- E-mails dos moradores são visíveis a todos os membros da casa.
- Os `placeholder` dos campos de e-mail em `entrar.html` e `cadastro.html` usam um endereço com aparência real; não o reproduza em documentação.
- Se o token CSRF expirar numa ação AJAX, o servidor responde HTML 400 e `app.js` mostra um erro de leitura de JSON em vez da mensagem "Sessao expirada".

### 12.3 Regras para agentes

- Não leia, imprima, copie para respostas nem inclua em commits os valores do `.env`.
- Não modifique `SECRET_KEY`, hash de senhas, políticas de sessão, CSRF, permissões ou acesso ao banco sem pedido explícito.
- **Nunca** crie, limpe, migre ou altere um banco existente sem autorização explícita. Não execute migrações automaticamente.
- Não execute testes que gravem dados no banco principal.
- Não instale pacotes, apague dados, altere a estrutura de pastas nem reescreva o front-end sem autorização.
- Não substitua a desativação de dispositivos (`ativo = 0`) por `DELETE`.
- Não prometa integração física com IoT nem segurança de produção.

### 12.4 Diálogos do navegador (testes manuais ou automatizados)

Formulários com `data-confirmar` (excluir cômodo, remover morador, remover dispositivo, excluir rotina) abrem `window.confirm`. Erros de AJAX abrem `window.alert`. O cadastro concluído exibe um pop-up HTML ("Conta criada"), acionado pelo texto da mensagem `flash`.

## 13. Estado da verificação

**Coberto por testes automatizados (com banco falso):** modelos e polimorfismo; validadores; `FilaRotinas`; `transacao()`; controle, cadastro e remoção de dispositivos (serviço); regras do executor (não repetir, rotina pausada depois de montar a fila, falha isolada, limite de 10 min quando `desde` é antigo, contexto do app); cômodos (criar, renomear, excluir, transferir); cadastro de morador e senha temporária; login com troca obrigatória e a troca de senha; salvar e editar rotinas; permissões das rotas de cômodos, transferência, moradores (cadastro) e rotinas (criar e editar); CSRF ausente; páginas públicas, painel e saída.

**Coberto por testes de integração (MySQL real, banco `habitus_testes`, aprovados em 09/11/2026):** conexão e existência exata das 7 tabelas; `INSERT`, `SELECT`, `UPDATE` e `DELETE` em `usuarios`; em `moradores`, recusa de usuário ou casa inexistente (1452) e de vínculo duplicado (1062). Usam SQL próprio: não exercitam `repositories` nem `services`.

**Verificado só na leitura do código (sem teste automatizado):**
- mudar perfil e remover morador;
- troca de casa (`/casa/selecionar`) e o retorno à primeira casa em `carregar_acesso`;
- pausar e excluir rotinas;
- página `/historico`;
- resposta JSON de `/dispositivos/<id>/controle` e as permissões das rotas `POST /dispositivos` e `/dispositivos/<id>/remover`;
- o laço de `executar_rotinas.py` e a janela de 1 minuto ao iniciar;
- o manipulador de erros;
- todo o JavaScript (`app.js`).

**Não verificado (depende do ambiente):**
- comportamento real do MySQL: bloqueios `FOR UPDATE` entre dois executores, `CHECK`, `ON DELETE` e collation;
- o SQL dos `repositories` executado num MySQL real;
- execução do site e do executor com um banco real;
- renderização no navegador, inclusive a fonte importada no CSS;
- o estado atual do protótipo no Figma.

## 14. Divergências conhecidas na documentação existente

Em 08/11/2026, o `README.md` e os documentos técnicos de `docs/` foram revisados e sincronizados com o código. As afirmações antigas foram corrigidas: o executor que "não perde execuções", a recuperação de 10 minutos ao reiniciar, os testes que "não precisam de MySQL" e o roteiro sem a classe `Generico`.

Em 09/11/2026, as referências aos resultados dos testes foram atualizadas em `README.md`, neste arquivo e em `docs/` (`README.md`, `TESTES.md`, `ARQUITETURA.md`, `BANCO_DE_DADOS.md`, `ROTEIRO_APRESENTACAO.md`): os 3 testes de integração deixaram de constar como não executados, e a suíte completa consta com `144 passed`.

Divergências que permanecem:

- `docs/TELAS_FIGMA.md` (material complementar de design, preservado como estava) não inclui a opção de cômodos iniciais nem a tela de troca de senha, e está sem acentos. Não o trate como descrição do front-end; para isso, use `docs/FRONTEND.md`. O estado do protótipo no Figma não foi conferido.
- `database/schema.sql`: o comentário "Dispositivos simulados ou conectados" sugere IoT real, que não existe. É um arquivo SQL; só altere com autorização.

Se o código mudar, os documentos afetados e esta seção precisam ser revisados.

## 15. Procedimento obrigatório para agentes de IA

1. Leia este `AGENTS.md` e identifique a solicitação exata do usuário.
2. Consulte os arquivos relacionados à tarefa e informe **quais foram realmente examinados** (por completo ou em parte).
3. Separe **funcionalidades verificadas no código**, **comportamentos ainda não testados** e **sugestões futuras**.
4. Antes de alterar algo, descreva a mudança e solicite autorização se ela ainda não tiver sido dada.
5. Limite a mudança autorizada ao menor conjunto de arquivos; preserve nomes, rotas, textos e regras existentes.
6. Verifique impactos em `routes`, `services`, `models`, `repositories`, `validators`, templates, `app.js`, esquema SQL, migrações e testes.
7. Mostre os caminhos dos arquivos afetados e as limitações de verificação.
8. Se o código mudar, atualize este arquivo com base nos arquivos efetivamente alterados.

## 16. Documentação existente — alterar somente quando solicitado

O projeto já contém o `README.md` principal e a documentação técnica em `docs/`. A presença deste arquivo **não autoriza** reescrevê-los.

| Assunto | Documento |
| --- | --- |
| Índice, visão geral, glossário e limitações consolidadas | `docs/README.md` |
| Camadas, ciclo da requisição, transações e Engenharia de Software | `docs/ARQUITETURA.md` |
| Classes, POO e estruturas de dados | `docs/ESTRUTURAS_E_POO.md` |
| Tabelas, restrições, migrações e banco de testes | `docs/BANCO_DE_DADOS.md` |
| Rotas, perfis e permissões | `docs/ROTAS_E_PERMISSOES.md` |
| Autenticação e segurança | `docs/AUTENTICACAO_E_SEGURANCA.md` |
| Executor de rotinas | `docs/EXECUTOR_ROTINAS.md` |
| Testes | `docs/TESTES.md` |
| Front-end | `docs/FRONTEND.md` |
| Apresentação acadêmica | `docs/ROTEIRO_APRESENTACAO.md` |
| Design no Figma (complementar, pendente de atualização) | `docs/TELAS_FIGMA.md` |

Quando houver pedido para atualizar o README ou a documentação técnica:

- Use como fontes principais o código, `database/schema.sql`, as migrações, `backend/requirements.txt` e `pytest.ini`. Use este arquivo, o README e `docs/` como apoio sujeito a conferência (veja a seção 14).
- Cada assunto tem um documento principal; nos demais, prefira um link a repetir a explicação.
- Informe o que já existe, o que está sendo atualizado e o que precisa de validação manual.
- Documente separadamente: instalação do MySQL e criação do banco, configuração do `.env`, execução do Flask, execução do executor de rotinas, perfis e rotas, classes, esquema e migrações, segurança, testes (isolados e de integração) e limitações.
- Não atribua ao sistema tecnologias inexistentes, endpoints não confirmados, integrações físicas, resultados de testes não executados ou funcionalidades planejadas.
- Mantenha a redação em português claro, com linguagem técnica adequada a um projeto acadêmico e a um portfólio.
