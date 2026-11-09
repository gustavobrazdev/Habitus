# Roteiro de apresentação do Habitus

Roteiro para apresentar o Habitus na ExpoTech 2026.2, projeto do 4º semestre de Ciência da Computação da UniFECAF. Cada parte indica o que mostrar, em quais arquivos ou telas, e quais pontos explicar. A ordem pode ser adaptada; não é preciso decorar frases, e sim saber o motivo de cada parte existir.

Os detalhes técnicos de cada assunto estão nos documentos indicados entre parênteses (índice em [README.md](README.md)).

## Preparação

Antes de apresentar:

- [ ] MySQL em execução e banco `habitus_smart_home` criado com `database/schema.sql`.
- [ ] Terminal 1: `python backend\run.py` → site em `http://127.0.0.1:5000`.
- [ ] Terminal 2: `python backend\executar_rotinas.py` (o executor de rotinas).
- [ ] Terminal 3, para os testes, com o ambiente virtual ativado.
- [ ] No VS Code, abertos: `backend/app/models/dispositivo.py`, `backend/app/structures/fila_rotinas.py`, `backend/app/services/rotinas.py`, `backend/app/services/dispositivos.py` e `database/schema.sql`.
- [ ] Um e-mail ainda sem conta, para cadastrar um morador durante a demonstração.
- [ ] O arquivo do Figma aberto, com os frames Lo-Fi e Hi-Fi e o Prototype no estado em que estiver.

## 1. Objetivo do sistema

- O Habitus é a central de uma casa inteligente **simulada**: os aparelhos não são reais, e o estado de cada um fica salvo no MySQL.
- Problemas que ele trata:
  - ver todos os aparelhos por cômodo;
  - automatizar ações por horário;
  - compartilhar a casa com perfis de acesso diferentes;
  - saber quem alterou o quê.
- Ele integra quatro disciplinas do 4º semestre:

  | Disciplina | Onde aparece neste roteiro |
  | --- | --- |
  | Python | Toda a aplicação: Flask, regras de negócio, executor e testes (partes 4, 8 e 10) |
  | Estrutura de Dados | Parte 6 |
  | Orientação a Objeto | Parte 5 |
  | Interface UX/UI (Figma) | Partes 2 e 3 |

- A arquitetura em camadas e os testes também mostram práticas de Engenharia de Software, apresentadas como boas práticas do projeto, e não como uma das disciplinas.

## 2. Principais funcionalidades (demonstração)

| Passo | Na tela | O que destacar |
| :---: | --- | --- |
| 1 | **Criar conta** com "Usar sugeridos" | A conta, a casa, o vínculo de administrador e os cômodos Sala, Quarto e Cozinha são criados numa única transação |
| 2 | **Painel** | Indicadores, aparelhos por cômodo e atividade recente |
| 3 | **Dispositivos**: ligar a luz e ajustar o brilho | O controle é enviado por JavaScript (AJAX) e a página é recarregada com o estado gravado; os limites do controle deslizante vêm da classe Python |
| 4 | **Histórico** | Valor anterior, valor novo e responsável de cada alteração |
| 5 | **Minha casa**: criar e renomear um cômodo; em Dispositivos, usar "Mover para" | A transferência preserva configurações, rotinas e histórico |
| 6 | **Validações**: criar um cômodo "sala" (já existe "Sala"); tentar excluir um cômodo com aparelhos | Mensagens "Ja existe um comodo com esse nome nesta casa." e "Transfira-os para outro ambiente antes de excluir." |

(Detalhes das telas: [FRONTEND.md](FRONTEND.md).)

## 3. Interface UX/UI (Figma)

**Mostrar:** o arquivo do Figma com os frames Lo-Fi e Hi-Fi e, ao lado, as telas reais do sistema em execução (ou as capturas do [README principal](../README.md#telas-do-sistema)).

**Explicar:**

- **Processo de design:** primeiro o Lo-Fi (estrutura, sem cores), depois o Hi-Fi (cores, cards e componentes) e, por fim, o Prototype, que liga os botões para mostrar o caminho do usuário ([TELAS_FIGMA.md](TELAS_FIGMA.md)).
- **Situação:** segundo o grupo, as etapas Lo-Fi e Hi-Fi foram concluídas; o Prototype **ainda está em finalização**. Apresente-o como etapa em andamento.
- **Do design ao código:** as cores do Hi-Fi seguem as variáveis do CSS (`--lateral`, `--azul`, `--fundo`, `--texto`), e as telas de login e cadastro usam classes com o sufixo `-figma` ([FRONTEND.md](FRONTEND.md#8-implementação-planejamento-visual-e-figma)).
- **Decisões de UX visíveis no sistema:**
  - confirmação antes de excluir ou remover;
  - mensagens de retorno depois de cada ação;
  - formulário de rotinas que mostra só as ações compatíveis com o aparelho;
  - formulários de gestão ocultos para o morador comum;
  - menu lateral que vira um menu recolhível em telas estreitas.
- **Limite:** a correspondência entre o protótipo e as telas implementadas não foi conferida nesta documentação, e o guia [TELAS_FIGMA.md](TELAS_FIGMA.md) ainda precisa ser atualizado (cômodos iniciais e troca de senha).

## 4. Arquitetura em camadas

**Mostrar:** a pasta `backend/app/` e o diagrama de dependências de [ARQUITETURA.md](ARQUITETURA.md#22-dependências-reais-entre-os-módulos).

**Explicar:**

- **As camadas:**

  | Camada | Responsabilidade |
  | --- | --- |
  | `routes` | Recebe o pedido HTTP |
  | `services` | Aplica as regras de negócio |
  | `validators` | Valida as entradas |
  | `models` | Representa os objetos |
  | `repositories` | Executa o SQL |
  | `structures` | Guarda a agenda das rotinas |

- **Separação de responsabilidades:** rotas não têm SQL, e repositórios não têm regras de negócio. O núcleo não depende do Flask, o que permite testá-lo sem servidor.
- **Transação:** em `services/dispositivos.py`, a função `salvar_alteracao()` grava o novo estado do aparelho e o histórico **na mesma transação**: ou as duas operações acontecem, ou nenhuma.

## 5. Orientação a Objeto

**Mostrar:** `backend/app/models/dispositivo.py`.

| Conceito | Onde apontar |
| --- | --- |
| Herança | `Dispositivo` → `Luz`, `Climatizador` (→ `ArCondicionado`, `Aquecedor`), `Ventilador` e **`Generico`**, o tipo "outro", que só liga e desliga |
| Reaproveitamento por herança | `ArCondicionado` e `Aquecedor` herdam todo o controle de temperatura de `Climatizador` e só mudam o `valor_inicial` (22 °C e 25 °C) |
| Encapsulamento | `_brilho` lido pela propriedade `brilho`; `ajustar_brilho()` valida antes de alterar |
| Polimorfismo | Todos respondem a `executar(acao, valor)`, cada um do seu jeito; o serviço não precisa saber o tipo |
| Abstração | O atributo `ajuste` guarda os limites de cada classe e é reaproveitado na validação, nas telas e no formulário de rotinas |

Mencione também `Usuario` (permissões), `Comodo` (nome validado) e `Rotina` (textos da tela). São 12 classes no total, contando `FilaRotinas` e `Config` ([ESTRUTURAS_E_POO.md](ESTRUTURAS_E_POO.md)).

## 6. Estrutura de Dados

| Estrutura | Arquivo | Uso |
| --- | --- | --- |
| `dict` | `models/dispositivo.py` (`CLASSES`) | Escolhe a classe pelo tipo salvo no banco, sem `if/elif` |
| `defaultdict(list)` | `services/casas.py` | Agrupa os dispositivos por cômodo no painel |
| `set` | `models/rotina.py` | Dias da semana de cada rotina |
| `tuple` | `structures/fila_rotinas.py` | Chave do heap: `(data e hora, id_rotina, rotina)` |
| `heapq` | `structures/fila_rotinas.py` | Fila de prioridade: a próxima rotina fica no topo |
| `deque` | `structures/fila_rotinas.py`, `services/rotinas.py` | Fila FIFO das rotinas que venceram |

Ponto de destaque: retirar a rotina mais próxima do heap custa O(log n), e `deque.popleft()` custa O(1), contra O(n) de `list.pop(0)`.

## 7. Banco MySQL

**Mostrar:** `database/schema.sql` e o diagrama de [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md#2-diagrama-entidade-relacionamento). No Workbench, uma chave estrangeira.

**Explicar:**

- **7 tabelas:** `usuarios`, `casas`, `moradores`, `comodos`, `dispositivos`, `historico` e `rotinas`.
- **Relação N:N:** usuários e casas se ligam por `moradores`, que guarda o perfil.
- **Integridade:**
  - `UNIQUE` impede e-mail repetido e nome de cômodo repetido na casa;
  - `CHECK` limita brilho, intensidade e temperatura;
  - `ON DELETE RESTRICT` impede apagar um cômodo com dispositivos.
- **Dispositivos nunca são apagados:** "remover" marca `ativo = 0`, preservando o histórico.

## 8. Rotinas automáticas

**Demonstração:** em **Rotinas**, crie uma rotina para um ou dois minutos à frente. No horário:

1. o terminal do executor mostra "Rotina executada: …";
2. o aparelho muda;
3. o histórico registra a ação com o responsável "Automação".

**Mostrar:** `backend/executar_rotinas.py` e `executar_pendentes()` em `backend/app/services/rotinas.py`.

**Explicar** ([EXECUTOR_ROTINAS.md](EXECUTOR_ROTINAS.md)):

- **Processo separado:** o executor roda num segundo processo e verifica a agenda a cada 20 segundos, aproximadamente.
- **Releitura com bloqueio:** antes de executar, a rotina é relida com `SELECT ... FOR UPDATE`. A coluna `ultima_execucao` evita executar duas vezes.
- **Limites de tempo:**
  - ao iniciar, o executor considera só o último minuto;
  - com o executor rodando, recupera atrasos de até 10 minutos;
  - rotinas do período em que esteve desligado não são executadas.

## 9. Perfis e permissões

**Demonstração:**

1. Em **Minha casa**, adicione um morador **comum** com um e-mail sem conta. A senha temporária aparece uma única vez; o sistema não envia e-mails.
2. Saia e entre com esse e-mail e a senha temporária. O sistema exige a troca de senha antes de liberar qualquer página.
3. Como morador comum, mostre que é possível controlar os aparelhos, mas que os formulários de gestão não aparecem.

**Explicar** ([ROTAS_E_PERMISSOES.md](ROTAS_E_PERMISSOES.md)):

- **Perfil por casa:** existem os perfis `administrador` e `comum`, e a mesma pessoa pode ter perfis diferentes em casas diferentes.
- **Proteção no servidor:** esconder um botão não basta. `@administrador_obrigatorio` responde 403, mesmo que o formulário seja enviado manualmente.
- **Isolamento entre casas:** todo registro é buscado junto com o `id_casa` da casa aberta, então trocar um id na URL não dá acesso a outra casa.
- **Segurança:** senhas guardadas como hash e token CSRF em todos os formulários ([AUTENTICACAO_E_SEGURANCA.md](AUTENTICACAO_E_SEGURANCA.md)).

## 10. Testes automatizados

**Executar no terminal 3:**

```powershell
python -m pytest -v --ignore=tests/test_integracao_mysql.py
```

**Explicar** ([TESTES.md](TESTES.md)):

- **Dois grupos:** são 144 testes, 141 isolados e 3 de integração.
  - Os isolados usam um **banco falso** (`tests/apoio_banco.py`), que registra os comandos SQL sem precisar do MySQL.
  - Os de integração exigem o banco separado `habitus_testes`.
- **Último resultado confirmado:** em 09/11/2026, a suíte completa (`python -m pytest -v`) teve **144 testes aprovados** — 141 isolados e 3 de integração no banco `habitus_testes`. Na apresentação, vale o resultado exibido na hora; o comando acima roda só os 141 isolados.
- **Aprovação não é cobertura:** se perguntarem, 144 testes aprovados não significam 100% do código testado; o projeto não mede cobertura ([TESTES.md](TESTES.md#93-aprovação-não-é-cobertura)).
- **Exemplos que se ligam às disciplinas:**
  - `test_polimorfismo_mesma_chamada_para_classes_diferentes` (Orientação a Objeto);
  - `test_fila_fifo_entrega_na_ordem_dos_horarios` (Estrutura de Dados);
  - `test_transacao_confirma_ou_desfaz_tudo` (prática de Engenharia de Software: a transação confirma ou desfaz tudo).
- **Python:** os próprios testes são escritos em Python com o pytest.

## 11. Limitações conhecidas

Apresente com clareza o que o sistema **não** faz ([índice](README.md#limitações-conhecidas)):

- não controla aparelhos reais nem tem integração com Alexa ou Google Home;
- não envia e-mails; não tem recuperação de senha nem criação de uma segunda casa;
- o executor precisa estar rodando, e rotinas perdidas durante uma interrupção não são recuperadas;
- é um projeto de demonstração local: sem HTTPS, com modo debug e sem limite de tentativas de login.

## Perguntas prováveis

| Pergunta | Resposta curta | Onde está |
| --- | --- | --- |
| Os aparelhos são reais? | Não; o estado é salvo no MySQL | [README.md](README.md#visão-geral-do-sistema) |
| O que acontece se o executor estiver desligado? | Nenhuma rotina roda; ao voltar, só o último minuto é considerado | [EXECUTOR_ROTINAS.md](EXECUTOR_ROTINAS.md#8-limites-de-tempo-e-exemplos) |
| Por que não apagar dispositivos? | Para não perder o histórico | [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md#54-regras-de-exclusão-on-delete) |
| Por que usar heap em vez de lista? | Encontrar a próxima rotina é O(1), e retirá-la, O(log n) | [ESTRUTURAS_E_POO.md](ESTRUTURAS_E_POO.md#14-análise-de-complexidade) |
| Como um morador comum é impedido de gerenciar? | Decorador no servidor, com resposta 403 | [ROTAS_E_PERMISSOES.md](ROTAS_E_PERMISSOES.md#43-os-decoradores) |
| Como as senhas são guardadas? | Como hash, com o padrão do Werkzeug (scrypt) | [AUTENTICACAO_E_SEGURANCA.md](AUTENTICACAO_E_SEGURANCA.md#4-senhas) |
| Como sei que o código funciona? | Testes automatizados com pytest | [TESTES.md](TESTES.md) |
| O protótipo do Figma está pronto? | Segundo o grupo, Lo-Fi e Hi-Fi foram concluídos; o Prototype ainda está em finalização | [TELAS_FIGMA.md](TELAS_FIGMA.md) |
