# Testes automatizados do Habitus

Este documento descreve a estratégia de testes do Habitus: a configuração do pytest, o banco falso, o conteúdo de cada arquivo de teste, os testes de integração com MySQL, os resultados confirmados e o que ainda não tem teste automatizado.

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Configuração do pytest](#2-configuração-do-pytest)
3. [O banco falso](#3-o-banco-falso)
4. [Testes isolados por arquivo](#4-testes-isolados-por-arquivo)
5. [Conceitos demonstrados pelos testes](#5-conceitos-demonstrados-pelos-testes)
6. [Testes de integração com MySQL](#6-testes-de-integração-com-mysql)
7. [Como executar](#7-como-executar)
8. [Como interpretar os resultados](#8-como-interpretar-os-resultados)
9. [Resultados confirmados](#9-resultados-confirmados)
10. [O que ainda não tem teste automatizado](#10-o-que-ainda-não-tem-teste-automatizado)
11. [Fontes](#11-fontes)

---

## 1. Visão geral

| Grupo | Arquivos | Testes coletados | Precisa de MySQL? |
| --- | :---: | :---: | :---: |
| Testes isolados | 8 | 141 | Não |
| Testes de integração | 1 | 3 | **Sim** |
| **Total** | 9 | **144** | — |

As contagens foram obtidas com `pytest --collect-only` em 08/11/2026 e coincidem com a execução completa de 09/11/2026 (`144 passed`; veja a [seção 9](#9-resultados-confirmados)). Cada caso de um teste parametrizado (`@pytest.mark.parametrize`) conta como um teste.

- **Testes isolados** substituem o MySQL por um banco falso. Eles verificam a lógica do Python: modelos, estruturas, validadores, serviços, rotas e templates. Rodam em cerca de 2 segundos.
- **Testes de integração** conectam a um MySQL real, no banco separado `habitus_testes`, e verificam o **esquema**: tabelas, chaves e restrições. Não chamam o código da aplicação.

## 2. Configuração do pytest

```ini
# pytest.ini
[pytest]
# Permite que os testes importem o pacote "app" que fica em backend/.
pythonpath = backend tests
testpaths = tests
```

| Opção | Efeito |
| --- | --- |
| `pythonpath = backend tests` | Inclui `backend/` e `tests/` no caminho de importação. Assim, os testes fazem `from app import criar_app` e `from apoio_banco import usar_banco_falso` sem instalar o projeto como pacote |
| `testpaths = tests` | `python -m pytest` procura testes somente em `tests/` |

O pytest é instalado por `backend/requirements.txt` (`pytest>=8,<10`). Não há `conftest.py`: as funções de apoio ficam em `tests/apoio_banco.py`, e as *fixtures* são definidas dentro de cada arquivo.

## 3. O banco falso

`tests/apoio_banco.py` permite testar serviços e rotas sem MySQL.

### 3.1 `CursorFalso`

| Recurso | Comportamento |
| --- | --- |
| `execute(sql, valores)` | Guarda o comando, com os espaços normalizados, e os parâmetros em `comandos` |
| `fetchone()` | Devolve, em ordem, as respostas da lista `um`; depois, `None` |
| `fetchall()` | Devolve, em ordem, as respostas da lista `todos`; depois, `[]` |
| `erro_no_insert=True` | Faz todo `INSERT` levantar `pymysql.err.IntegrityError(1062, ...)`, simulando um `UNIQUE` violado |
| `lastrowid` | Aumenta a cada `execute`, simulando os ids gerados |
| `rowcount` | Sempre `1` |
| `sql(inicio)` | Filtra os comandos que começam com um texto, por exemplo `cursor.sql("INSERT INTO rotinas")` |

### 3.2 Funções de apoio

| Função | Papel |
| --- | --- |
| `transacao_com(cursor)` | Cria um substituto de `app.database.transacao` que entrega sempre o mesmo cursor falso |
| `usar_banco_falso(monkeypatch, *modulos, **respostas)` | Troca o nome `transacao` nos módulos de serviço indicados e devolve o cursor, para que o teste confira os SQL executados |
| `entrar_como(app, perfil, **sessao_extra)` | Cria um cliente de teste com `usuario_id = 9`, `casa_id = 7` e um token CSRF; devolve também um `patch` de `app.carregar_acesso` com o perfil desejado |

Exemplo de uso:

```python
# tests/test_servicos.py
def test_alteracao_grava_estado_e_historico(monkeypatch):
    cursor = usar_banco_falso(monkeypatch, servico_dispositivos, um=[dict(LUZ)])

    resultado = servico_dispositivos.alterar_dispositivo(5, 2, 9, "ajustar_brilho", "45")
    assert resultado == {"campo": "brilho", "antes": 80, "depois": 45}
    assert len(cursor.comandos) == 3  # SELECT, UPDATE, INSERT historico
    assert "FOR UPDATE" in cursor.comandos[0][0]
```

O banco falso funciona porque os serviços importam `transacao` com `from app.database import transacao`. O `monkeypatch` substitui esse nome **dentro do módulo do serviço**, e os repositórios recebem o cursor falso sem perceber a diferença.

### 3.3 Como as transações são testadas

O substituto de `transacao` não faz `commit` nem `rollback`; ele apenas entrega o cursor. O comportamento real de `transacao()` é testado à parte, em `test_transacao_confirma_ou_desfaz_tudo`, com uma conexão falsa que registra a sequência de eventos:

- sem erro: `execute` → `commit` → `close`;
- com erro: `execute` → `rollback` → `close`.

### 3.4 Limites do banco falso

- **Não executa SQL:** não detecta erros de sintaxe nem aplica restrições (`CHECK`, chaves estrangeiras, `UNIQUE`), exceto a simulação de `IntegrityError` em `INSERT`.
- **Respostas em ordem:** as respostas seguem a ordem programada no teste. Se um serviço passar a consultar em outra ordem, o teste precisa ser ajustado.
- **Sem bloqueios nem concorrência:** não simula `FOR UPDATE`; só verifica que o texto do SQL contém a cláusula.
- **`rowcount` fixo:** é sempre 1, então o caso "nenhuma linha alterada" não é simulado.

## 4. Testes isolados por arquivo

### `test_modelos.py` — 14 testes

Classes de dispositivos e de usuário (`backend/app/models/`):

- ajustes válidos e inválidos de brilho, temperatura e intensidade;
- encapsulamento: valor inválido não altera o objeto;
- configuração inicial por classe; ações herdadas e ampliadas; polimorfismo de `executar()`; limites vindos do atributo `ajuste`;
- permissões de `Usuario`; dias da semana; regra de não repetir uma rotina no mesmo horário.

### `test_estruturas.py` — 10 testes

`FilaRotinas`, `heapq` e `deque`:

- a rotina mais próxima fica no topo, com desempate por id;
- a fila entrega as rotinas em ordem FIFO;
- respeita os dias e `ultima_execucao`; não antecipa execuções;
- verificação atrasada não perde comandos; a rotina da meia-noite não se perde;
- uma execução no dia anterior não impede a de hoje;
- rotinas antes das 10h executam, porque `str(timedelta(hours=8))` é `"8:00:00"`, sem o zero à esquerda.

### `test_validadores.py` — 14 testes

Validadores de `backend/app/validators/`:

- texto com espaços normalizados e tamanho;
- identificadores inválidos (6 casos parametrizados);
- números inteiros e decimais, inclusive `nan`, `inf`, vírgula e casas decimais;
- e-mail, senha e perfil; nome de cômodo e opção de cômodos iniciais; dispositivo; horário e dias; rotina completa.

### `test_servicos.py` — 17 testes

Serviços de dispositivos e do executor, com o banco falso:

- `transacao()`: commit e rollback;
- controle de brilho e temperatura gravando o estado e o histórico;
- valor inválido sem escrita; dispositivo de outra casa;
- cadastro com a configuração da classe (3 casos inválidos); cômodo de outra casa;
- remoção com pausa das rotinas;
- executor: execução com histórico sem usuário, não repetição, rotina pausada depois de montada a fila, isolamento de falhas, limite de 10 minutos e uso do contexto da aplicação.

### `test_comodos.py` — 37 testes

Cômodos e transferência:

- modelo `Comodo`: normalização, 5 nomes inválidos, comparação sem maiúsculas;
- criar, inclusive nomes repetidos (3 casos) e `UNIQUE` do banco;
- renomear, excluir (com dispositivos ativos ou só removidos) e isolamento entre casas;
- transferência sem perda de dados;
- 403 para o perfil comum em 4 rotas; redirecionamento sem login;
- opções de cômodos iniciais no cadastro.

### `test_moradores.py` — 14 testes

Moradores e senha temporária:

- senha temporária aleatória e legível; conta nova com hash e `trocar_senha`;
- vínculo de conta existente; vínculo repetido; cadastro simultâneo com rollback;
- dados inválidos sem acesso ao banco; nome obrigatório para conta nova;
- senha exibida uma única vez, com `Cache-Control: no-store`; 403 para o perfil comum;
- login com troca obrigatória; conta anterior à migração; bloqueio de páginas e liberação após a troca.

### `test_rotinas.py` — 26 testes

Rotinas pelo site:

- textos do cartão (`Rotina`) com dados no formato do MySQL (`timedelta`, `Decimal`);
- descrição de 5 ações; valor para o formulário de edição; horário e dias;
- criação com ajuste sem executar (3 tipos); ligar e desligar sem valor; 4 valores ou ações inválidos;
- dispositivo e rotina de outra casa; edição da mesma rotina;
- página de lista sem botões de gestão para o perfil comum; formulário de edição preenchido; envio da edição;
- erro com status 400 e campos preservados; 403 para o perfil comum em 3 rotas.

### `test_paginas.py` — 9 testes

Páginas e fluxo entre as camadas:

- telas de login e cadastro; painel exige login; POST sem token CSRF → 400; 403 para o perfil comum;
- painel agrupando dispositivos por cômodo, com "Automação" no histórico;
- página de dispositivos com os limites das classes;
- cadastro e login passando por rota, serviço e repositório; saída limpando a sessão.

## 5. Conceitos demonstrados pelos testes

| Área | Conceito | Exemplo |
| --- | --- | --- |
| Engenharia de Software | Testes de unidade independentes de infraestrutura | Todo `test_modelos.py`, `test_estruturas.py` e `test_validadores.py` |
| Engenharia de Software | Dublês de teste (*test doubles*) e injeção de dependência | `CursorFalso`, `monkeypatch` de `transacao` e funções `proibido()` que falham se o serviço for chamado |
| Engenharia de Software | Classes de equivalência e valores-limite | Brilho `101`, temperatura `15.9` e `22.55`, nome com 81 caracteres, via `@pytest.mark.parametrize` |
| Engenharia de Software | Teste de regressão | `test_rotina_antes_das_dez_horas_tambem_executa` |
| Engenharia de Software | Integração entre camadas sem banco | `test_cadastro_e_login_passando_pelas_camadas` |
| Engenharia de Software | Verificação de segurança | CSRF, 403 por perfil e isolamento entre casas |
| POO | Herança, encapsulamento e polimorfismo | `test_acoes_permitidas_sao_herdadas_e_ampliadas`, `test_encapsulamento_mantem_o_valor_valido`, `test_polimorfismo_mesma_chamada_para_classes_diferentes` |
| Estruturas de Dados | Heap, fila FIFO e conjuntos | `test_heap_deixa_a_rotina_mais_proxima_no_topo`, `test_fila_fifo_entrega_na_ordem_dos_horarios`, `test_horario_e_dias` |

A relação completa entre cada conceito e seus testes está em [ESTRUTURAS_E_POO.md](ESTRUTURAS_E_POO.md#17-estado-da-verificação-e-fontes) e em [ROTAS_E_PERMISSOES.md](ROTAS_E_PERMISSOES.md#9-estado-da-verificação-e-fontes).

## 6. Testes de integração com MySQL

`tests/test_integracao_mysql.py` contém 3 testes que conectam a um MySQL real:

| Teste | Verifica |
| --- | --- |
| `test_conexao_mysql` | A conexão abre no banco `habitus_testes`, e as tabelas são **exatamente** as 7 do esquema |
| `test_crud_usuarios_mysql` | `INSERT`, `SELECT`, `UPDATE` e `DELETE` em `usuarios`, com um e-mail aleatório terminado em `@example.invalid` |
| `test_relacionamentos_mysql` | Com `FOREIGN_KEY_CHECKS` ativo: vínculos de perfis diferentes em duas casas; recusa de usuário e de casa inexistentes (erro **1452**); recusa de vínculo duplicado (erro **1062**) |

### 6.1 Cuidados com o banco principal

- **Banco separado:** o nome `habitus_testes` está fixo nos três testes; eles nunca usam `DB_NAME`.
- **Conferência antes de gravar:** os testes que gravam executam `SELECT DATABASE()` e conferem o nome do banco antes de qualquer `INSERT`.
- **Tudo é desfeito:** usam `autocommit=False` e chamam `conexao.rollback()` num bloco `finally`, mesmo se o teste falhar.
- **Dados reconhecíveis:** os e-mails gerados usam `uuid4()` e o domínio reservado `example.invalid`.

### 6.2 Pré-requisitos

1. MySQL 8.0.16+ em execução.
2. Banco `habitus_testes` com as 7 tabelas, criado manualmente a partir de uma cópia do `schema.sql` (veja [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md#10-banco-de-testes)). Nenhum script do projeto o cria.
3. `DB_USER` e `DB_PASSWORD` definidos no `.env` **da raiz do projeto**. O arquivo de teste carrega `RAIZ / ".env"` ao ser importado e não lê `backend/.env`. As credenciais são as mesmas do banco principal.

Sem esses pré-requisitos, os testes **falham** (`FAILED`); eles não são pulados automaticamente. Por isso, `python -m pytest -v` sem a opção `--ignore` termina com falhas numa máquina sem o banco de testes.

### 6.3 Situação

Os três testes foram **executados e aprovados em 09/11/2026**, no banco separado `habitus_testes`: `3 passed in 0.50s`. Detalhes e limites desse resultado estão na [seção 9](#9-resultados-confirmados).

## 7. Como executar

Todos os comandos partem da raiz do projeto, com o ambiente virtual ativado (`.\.venv\Scripts\Activate.ps1`).

| Objetivo | Comando (PowerShell) |
| --- | --- |
| Todos os testes isolados | `python -m pytest -v --ignore=tests/test_integracao_mysql.py` |
| Saída resumida | `python -m pytest -q --ignore=tests/test_integracao_mysql.py` |
| Um arquivo | `python -m pytest -v tests/test_modelos.py` |
| POO e Estruturas de Dados | `python -m pytest -v tests/test_modelos.py tests/test_estruturas.py` |
| Um teste específico | `python -m pytest -v "tests/test_modelos.py::test_permissoes"` |
| Testes cujo nome contém um termo | `python -m pytest -v -k "rotina" --ignore=tests/test_integracao_mysql.py` |
| Listar sem executar | `python -m pytest --collect-only -q` |
| Integração (somente com os pré-requisitos da seção 6.2) | `python -m pytest -v tests/test_integracao_mysql.py` |

Os casos parametrizados têm nomes com colchetes, como `tests/test_validadores.py::test_identificador_invalido[abc]`. No PowerShell, coloque o identificador entre aspas.

### 7.1 Arquivos de cache

O pytest e o Python criam arquivos auxiliares:

| Pasta | Conteúdo | Ignorada pelo `.gitignore` |
| --- | --- | :---: |
| `.pytest_cache/` | Lista dos testes e das últimas falhas, usada por `--lf` (rodar só o que falhou) | Sim |
| `__pycache__/` | Arquivos `.pyc` compilados, inclusive os gerados pelo pytest para reescrever as asserções | Sim |

Os dois podem ser apagados sem risco; são recriados na próxima execução. Para uma execução que não grave nada no projeto, por exemplo numa análise somente leitura:

```powershell
python -B -m pytest -p no:cacheprovider -q --ignore=tests/test_integracao_mysql.py
```

`-B` impede a criação de `.pyc`, e `-p no:cacheprovider` desativa o `.pytest_cache`. Para recomeçar com o cache limpo, use `--cache-clear`.

## 8. Como interpretar os resultados

| Resultado | Letra em `-q` | Significado | Exemplo no Habitus |
| --- | :---: | --- | --- |
| `PASSED` | `.` | Todas as asserções do teste foram verdadeiras | Execução normal dos 141 isolados e, com o banco `habitus_testes` disponível, dos 3 de integração |
| `FAILED` | `F` | Uma asserção falhou ou o **corpo** do teste levantou uma exceção | Testes de integração sem MySQL: a conexão levanta `OperationalError`; sem `DB_USER` no `.env`, `KeyError` |
| `ERROR` | `E` | O erro ocorreu **fora** do corpo do teste: numa *fixture*, na preparação ou ao importar o arquivo | Um erro de importação no pacote `app` aparece como erro de coleta |

O resumo final informa a contagem de cada tipo, por exemplo `144 passed in 2.47s`. Com `-v`, cada teste aparece numa linha com o seu resultado. Uma falha mostra a asserção e os valores comparados, o que normalmente basta para encontrar a causa.

## 9. Resultados confirmados

### 9.1 Resultado atual (09/11/2026)

| Execução | Comando (PowerShell, na raiz do projeto) | Resultado |
| --- | --- | --- |
| Testes de integração com MySQL, no banco `habitus_testes` | `python -m pytest -v tests/test_integracao_mysql.py` | **`3 passed in 0.50s`** |
| Suíte completa (isolados + integração) | `python -m pytest -v` | **`144 passed in 2.47s`** |

- **Total aprovado:** 144 testes — 141 isolados e 3 de integração. Nenhuma falha, erro ou teste pulado.
- **Ambiente:** Python 3.14.6 e pytest 9.2.0.
- **Banco usado pela integração:** o banco separado `habitus_testes`, criado manualmente com as 7 tabelas, conforme a [seção 6.2](#62-pré-requisitos). O banco principal `habitus_smart_home` não foi usado pelos testes.

O que a aprovação dos testes de integração confirma, num MySQL real: a conexão com o `habitus_testes` e a existência de **exatamente** as 7 tabelas; `INSERT`, `SELECT`, `UPDATE` e `DELETE` em `usuarios`; e, em `moradores`, a recusa de usuário ou casa inexistente (erro 1452) e de vínculo duplicado (erro 1062), com `FOREIGN_KEY_CHECKS` ativo.

O que ela **não** confirma: o SQL dos repositórios e serviços (os testes de integração usam SQL próprio), as restrições `CHECK`, as regras `RESTRICT`, `CASCADE` e `SET NULL`, os bloqueios `FOR UPDATE` sob concorrência nem a estrutura do banco principal. Veja a [seção 10](#10-o-que-ainda-não-tem-teste-automatizado).

### 9.2 Histórico de verificações anteriores

Resultados registrados antes da execução de 09/11/2026. Ficam aqui como histórico; o resultado atual é o da seção 9.1.

| Data | Execução | Resultado |
| --- | --- | --- |
| 08/11/2026 | Testes isolados, em várias etapas da documentação | `141 passed` |
| 08/11/2026, 19:05 | Testes isolados, com `python -B -m pytest -p no:cacheprovider -q --ignore=tests/test_integracao_mysql.py` | `141 passed in 1.92s` |
| 08/11/2026 | Testes de integração com MySQL | Não executados nessa data |

Ambiente das execuções de 08/11/2026: Python 3.14.6, pytest 9.2.0, Flask 3.1.3, Werkzeug 3.1.9 e PyMySQL 1.2.3.

### 9.3 Aprovação não é cobertura

Os 144 testes aprovados mostram que todas as asserções escritas foram verdadeiras. Isso **não** significa que 100% do código foi exercitado: há rotas, serviços, o laço do executor e todo o JavaScript sem teste automatizado (seção 10).

O projeto não mede **cobertura de código** (não há `pytest-cov` nas dependências). Por isso, este documento não apresenta porcentagens de cobertura.

## 10. O que ainda não tem teste automatizado

| Área | Sem teste específico |
| --- | --- |
| Rotas | Resposta JSON de `/dispositivos/<id>/controle`; 403 em `POST /dispositivos`, `/dispositivos/<id>/remover`, `/rotinas/<id>/alternar`, `/rotinas/<id>/remover`, `/casa/moradores/<id>/perfil` e `/casa/moradores/<id>/remover`; troca de casa (`/casa/selecionar`); página `/historico`; manipulador de erros |
| Serviços | `mudar_perfil`, `remover_morador`, `alternar_rotina`, `remover_rotina`, `carregar_acesso` (sempre substituído nos testes de rota), `pode_abrir_casa`, `historico_da_casa` |
| Segurança | Token CSRF **incorreto** (só o ausente é testado); cabeçalho `X-CSRF-Token`; atributos do cookie de sessão |
| Executor | O laço de `backend/executar_rotinas.py`; a janela de 1 minuto na primeira verificação; a ausência de nova tentativa para falhas individuais |
| Banco | SQL executado num MySQL real; `CHECK`, `RESTRICT`, `CASCADE` e `SET NULL`; bloqueios sob concorrência. Os testes de integração, aprovados em 09/11/2026, cobrem só `usuarios` e as chaves de `moradores` |
| Front-end | Todo o `app.js`, o CSS e o comportamento no navegador. Não há testes de JavaScript nem de interface |

## 11. Fontes

Conferido em 08/11/2026: `pytest.ini`, `backend/requirements.txt`, `.gitignore`, `tests/apoio_banco.py`, `tests/test_modelos.py`, `tests/test_estruturas.py`, `tests/test_validadores.py`, `tests/test_servicos.py`, `tests/test_comodos.py`, `tests/test_moradores.py`, `tests/test_rotinas.py`, `tests/test_paginas.py`, `tests/test_integracao_mysql.py`, `backend/app/database.py`.

Resultados de 09/11/2026 (seção 9.1): saídas do terminal das execuções feitas no ambiente local do projeto, com o banco `habitus_testes`.
