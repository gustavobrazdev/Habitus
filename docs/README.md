# Documentação técnica do Habitus

Esta pasta reúne a documentação técnica do **Habitus — Smart Home 2050**, projeto acadêmico do 4º semestre de Ciência da Computação da UniFECAF, apresentado na ExpoTech 2026.2. Ela explica como o sistema foi construído, por que foi construído assim e quais são os seus limites.

- Para uma apresentação geral, instalação e execução, comece pelo [README principal](../README.md).
- Para regras de trabalho de agentes de IA e a referência técnica condensada, veja o [AGENTS.md](../AGENTS.md).
- Em caso de divergência entre qualquer documento e o código, **o código prevalece**.

## Sumário

- [Documentos](#documentos)
- [Disciplinas e documentos](#disciplinas-e-documentos)
- [Ordem de leitura sugerida](#ordem-de-leitura-sugerida)
- [Visão geral do sistema](#visão-geral-do-sistema)
- [Glossário](#glossário)
- [Limitações conhecidas](#limitações-conhecidas)
- [Convenções desta documentação](#convenções-desta-documentação)

## Documentos

| Documento | Finalidade | Situação |
| --- | --- | --- |
| `README.md` (este arquivo) | Índice, visão geral, glossário e limitações consolidadas | Concluído em 08/11/2026; resultados dos testes atualizados em 09/11/2026 |
| [ARQUITETURA.md](ARQUITETURA.md) | Organização em camadas, dependências, ciclo da requisição, transações e conceitos de Engenharia de Software | Concluído em 08/11/2026; resultados dos testes atualizados em 09/11/2026 |
| [ESTRUTURAS_E_POO.md](ESTRUTURAS_E_POO.md) | As 12 classes, herança, encapsulamento, polimorfismo e as estruturas de dados, com `FilaRotinas` e análise de complexidade | Concluído em 08/11/2026 |
| [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md) | As 7 tabelas, relacionamentos, restrições, regras de exclusão, transações, migrações e banco de testes | Concluído em 08/11/2026; resultados dos testes atualizados em 09/11/2026 |
| [ROTAS_E_PERMISSOES.md](ROTAS_E_PERMISSOES.md) | As 26 declarações de rota, matriz de permissões, isolamento entre casas, respostas e códigos HTTP | Concluído em 08/11/2026 |
| [AUTENTICACAO_E_SEGURANCA.md](AUTENTICACAO_E_SEGURANCA.md) | Cadastro, login, senhas, sessão, CSRF, senha temporária, proteções e limitações de segurança | Concluído em 08/11/2026 |
| [EXECUTOR_ROTINAS.md](EXECUTOR_ROTINAS.md) | O processo `executar_rotinas.py`, o agendamento, as falhas, os limites de tempo e o fuso horário | Concluído em 08/11/2026 |
| [TESTES.md](TESTES.md) | Configuração do pytest, banco falso, cada arquivo de teste, integração com MySQL, resultados e lacunas | Atualizado em 09/11/2026 (144 testes aprovados) |
| [FRONTEND.md](FRONTEND.md) | Templates Jinja, telas por perfil, CSS e responsividade, JavaScript e comunicação com o back-end | Concluído em 08/11/2026 |
| [ROTEIRO_APRESENTACAO.md](ROTEIRO_APRESENTACAO.md) | Roteiro da apresentação acadêmica, ligado aos arquivos e às telas reais | Concluído em 08/11/2026; resultados dos testes atualizados em 09/11/2026 |
| [TELAS_FIGMA.md](TELAS_FIGMA.md) | Material complementar: guia para desenhar as telas no Figma | Pendente de atualização: não cita a opção de cômodos iniciais nem a tela de troca de senha |
| [diagramas/README.md](diagramas/README.md) | Índice dos diagramas: os novos desta pasta e o mapa dos diagramas que já existiam nos outros documentos | Criado em 11/11/2026 |
| [diagramas/CASOS_DE_USO.md](diagramas/CASOS_DE_USO.md) | Diagrama UML de casos de uso: Visitante, MORADOR (`comum`), ADMIN (`administrador`) e Executor de rotinas, com rastreabilidade até rotas, permissões e testes | Criado em 11/11/2026 |
| [diagramas/SEQUENCIA_TRANSFERIR_DISPOSITIVO.md](diagramas/SEQUENCIA_TRANSFERIR_DISPOSITIVO.md) | Diagrama UML de sequência da transferência de um dispositivo entre cômodos, do formulário ao MySQL | Criado em 11/11/2026 |
| [diagramas/ORGANIZACAO_TESTES.md](diagramas/ORGANIZACAO_TESTES.md) | Diagramas da organização dos 144 testes: grupos, categorias, arquivos, componentes verificados e lacunas | Criado em 11/11/2026 |

`TELAS_FIGMA.md` não faz parte da documentação técnica do código: é um guia de design, preservado como estava. O estado do protótipo no Figma não foi conferido nesta documentação; segundo o grupo, as etapas Lo-Fi e Hi-Fi foram concluídas e o Prototype ainda está em finalização.

## Disciplinas e documentos

O projeto integra quatro disciplinas:

| Disciplina | Onde ver |
| --- | --- |
| Python | [ARQUITETURA.md](ARQUITETURA.md) (organização do back-end em Flask), [EXECUTOR_ROTINAS.md](EXECUTOR_ROTINAS.md) e [TESTES.md](TESTES.md) (pytest) |
| Estrutura de Dados | [ESTRUTURAS_E_POO.md](ESTRUTURAS_E_POO.md), Parte 2 |
| Orientação a Objeto | [ESTRUTURAS_E_POO.md](ESTRUTURAS_E_POO.md), Parte 1 |
| Interface UX/UI (Figma) | [FRONTEND.md](FRONTEND.md#8-implementação-planejamento-visual-e-figma) e [TELAS_FIGMA.md](TELAS_FIGMA.md) (material complementar, pendente de atualização) |

Os conceitos de Engenharia de Software descritos em [ARQUITETURA.md](ARQUITETURA.md#7-conceitos-de-engenharia-de-software) e [TESTES.md](TESTES.md#5-conceitos-demonstrados-pelos-testes) são práticas usadas na organização do código, e não uma das disciplinas.

## Ordem de leitura sugerida

| Objetivo do leitor | Caminho |
| --- | --- |
| Entender o sistema rapidamente | Este índice → [ARQUITETURA.md](ARQUITETURA.md) |
| Avaliar os conceitos das disciplinas | [ESTRUTURAS_E_POO.md](ESTRUTURAS_E_POO.md) (Orientação a Objeto e Estrutura de Dados) → [EXECUTOR_ROTINAS.md](EXECUTOR_ROTINAS.md) (as estruturas em uso) → [ARQUITETURA.md](ARQUITETURA.md) (Python e práticas de Engenharia de Software) → [FRONTEND.md](FRONTEND.md) (Interface UX/UI); mapa completo em [Disciplinas e documentos](#disciplinas-e-documentos) |
| Preparar a apresentação | [ROTEIRO_APRESENTACAO.md](ROTEIRO_APRESENTACAO.md) |
| Instalar, executar e testar | [README principal](../README.md) → [TESTES.md](TESTES.md) → [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md) |
| Revisar segurança e permissões | [ROTAS_E_PERMISSOES.md](ROTAS_E_PERMISSOES.md) → [AUTENTICACAO_E_SEGURANCA.md](AUTENTICACAO_E_SEGURANCA.md) |
| Trabalhar no visual | [FRONTEND.md](FRONTEND.md) → [TELAS_FIGMA.md](TELAS_FIGMA.md) (material complementar) |
| Ver o sistema em diagramas UML | [diagramas/README.md](diagramas/README.md) → [CASOS_DE_USO.md](diagramas/CASOS_DE_USO.md) → [SEQUENCIA_TRANSFERIR_DISPOSITIVO.md](diagramas/SEQUENCIA_TRANSFERIR_DISPOSITIVO.md) → [ORGANIZACAO_TESTES.md](diagramas/ORGANIZACAO_TESTES.md) |

## Visão geral do sistema

### Objetivo

O Habitus simula a central de uma casa inteligente. Ele permite organizar cômodos, controlar aparelhos, compartilhar a casa com outras pessoas, automatizar ações por horário e consultar o histórico de alterações. Os aparelhos são **simulados**: o estado de cada um fica salvo no MySQL, e não há integração com equipamentos físicos, Alexa ou Google Home.

### Como funciona

O sistema é formado por **dois processos Python** que compartilham o mesmo código (`backend/app/`) e o mesmo banco MySQL:

| Processo | Arquivo | Papel |
| --- | --- | --- |
| Servidor web | `backend/run.py` | Atende o navegador em `http://127.0.0.1:5000`, renderiza as páginas e aplica as regras de negócio |
| Executor de rotinas | `backend/executar_rotinas.py` | A cada 20 segundos, procura rotinas cujo horário chegou e as executa |

Os dois processos não se comunicam diretamente; o que um grava no banco, o outro lê. Os detalhes estão em [ARQUITETURA.md](ARQUITETURA.md#1-visão-geral-da-execução).

### Módulos funcionais

| Módulo | Resumo | Onde está a regra |
| --- | --- | --- |
| Autenticação | Cadastro de conta e casa, login, logout, troca obrigatória da senha temporária | `backend/app/services/autenticacao.py` |
| Casas | Uma pessoa pode participar de várias casas, com perfil diferente em cada uma | `backend/app/services/casas.py` |
| Cômodos | Criar, renomear, excluir e transferir dispositivos entre cômodos | `backend/app/services/comodos.py` |
| Dispositivos | Cadastrar, ligar, desligar, ajustar e desativar | `backend/app/services/dispositivos.py` |
| Moradores | Vincular contas existentes ou criar contas com senha temporária; mudar perfil; remover acesso | `backend/app/services/moradores.py` |
| Rotinas | Cadastrar, editar, pausar, excluir e executar ações programadas | `backend/app/services/rotinas.py` |
| Painel e histórico | Resumo da casa e registro das alterações | `backend/app/services/casas.py` |

### O Habitus em números

Contagens feitas diretamente no código em 08/11/2026:

| Item | Quantidade |
| --- | --- |
| Rotas Flask (funções de rota) | 26, em 6 blueprints |
| Classes em `backend/app/` | 12 (7 de dispositivos, `Usuario`, `Comodo`, `Rotina`, `FilaRotinas` e `Config`) |
| Serviços / repositórios / validadores | 6 / 7 / 5 arquivos |
| Tabelas no MySQL | 7 |
| Templates HTML | 9 |
| Testes automatizados | 144 (141 isolados e 3 de integração com MySQL), todos aprovados em 09/11/2026 |

## Glossário

| Termo | Significado no Habitus |
| --- | --- |
| **Casa** | Residência cadastrada (tabela `casas`). Toda conta nasce com uma casa. |
| **Casa aberta** | A casa que a pessoa está usando no momento, guardada em `session["casa_id"]`. Todas as operações valem para ela. |
| **Morador** | Vínculo entre um usuário e uma casa (tabela `moradores`), com um perfil. |
| **Perfil** | `administrador` (gerencia a casa) ou `comum` (usa a casa). É definido por casa, não por conta. |
| **Cômodo** | Ambiente da casa (Sala, Quarto...). Nome único por casa, sem diferenciar maiúsculas. |
| **Dispositivo** | Aparelho simulado de um tipo: `luz`, `ar_condicionado`, `aquecedor`, `ventilador` ou `outro`. |
| **Ajuste** | Controle extra de um tipo de dispositivo: brilho, temperatura ou intensidade. |
| **Desativação** | Forma de "remover" um dispositivo: `ativo = 0`, preservando o histórico. |
| **Rotina** | Ação programada (ligar, desligar ou ajustar) para um horário e dias da semana. |
| **Executor** | O processo `executar_rotinas.py`, que executa as rotinas no horário. |
| **Histórico** | Registro de cada alteração de dispositivo, com valor anterior, novo e responsável. |
| **Transação** | Conjunto de comandos SQL confirmados juntos (`commit`) ou desfeitos juntos (`rollback`). |
| **Banco falso** | `tests/apoio_banco.py`: substitui o MySQL nos testes isolados e registra os comandos SQL. |

## Limitações conhecidas

Lista consolidada. Cada documento temático detalha as limitações do seu assunto.

**Escopo**

- Dispositivos simulados; sem integração física, Alexa ou Google Home.
- Sem envio de e-mails: a senha temporária de um morador é entregue pessoalmente.
- Feito para desenvolvimento e demonstração local; não está preparado para produção.

**Funcionalidades ausentes**

- Criar uma segunda casa, renomear ou excluir uma casa.
- Recuperar a senha, trocá-la voluntariamente ou excluir a conta.
- Restaurar um dispositivo removido.
- Excluir um cômodo ao qual esteja ligado um dispositivo removido (ele guarda o histórico e não pode ser transferido nem restaurado). Cômodos cujos dispositivos foram todos transferidos podem ser excluídos.
- Consultar na tela mais do que as 100 alterações mais recentes do histórico.
- Uma conta sem vínculo com nenhuma casa consegue autenticar, mas a sessão é encerrada na requisição seguinte, sem mensagem.

**Executor de rotinas**

- Precisa estar rodando em um terminal separado.
- Ao iniciar, considera só o último minuto; com o processo em execução, recupera atrasos de no máximo 10 minutos.
- Usa a hora local do computador, enquanto a data do histórico é gravada pelo MySQL.

**Segurança**

- Sem `.env`, o sistema usa uma chave de sessão fixa e o usuário `root` sem senha.
- `run.py` usa `debug=True`.
- O manipulador dos erros 400, 403 e 404 insere a descrição do erro no HTML sem escape (hoje só recebe textos fixos).
- Sem limite de tentativas de login, HTTPS, cookie `Secure` ou expiração de sessão configurada; senha mínima de 8 caracteres.
- Todos os membros de uma casa veem os e-mails dos demais moradores.

**Banco e testes**

- O nome `habitus_smart_home` está fixo nos scripts SQL; o banco `habitus_testes` não é criado por nenhum script.
- Os testes de integração leem só o `.env` da raiz e não são pulados sem MySQL. Foram aprovados em 09/11/2026 no banco `habitus_testes`, mas cobrem só o esquema de `usuarios` e as chaves de `moradores`, com SQL próprio.
- O projeto não mede cobertura de código: os 144 testes aprovados não significam que 100% do código foi testado.
- Não há testes de JavaScript nem de interface no navegador.

**Arquitetura**

- Cada chamada de serviço abre uma nova conexão com o MySQL, sem reaproveitamento de conexões. Veja [ARQUITETURA.md](ARQUITETURA.md#8-decisões-de-projeto-e-consequências).

## Convenções desta documentação

- **Fonte da verdade:** o código. Os documentos citam arquivos e funções para que tudo possa ser conferido.
- **Caminhos:** relativos à raiz do projeto (`Habitus/`), por exemplo `backend/app/services/rotinas.py`.
- **Estado da verificação:** cada documento termina com uma seção que separa:
  - **Testado** — coberto por teste automatizado que foi executado e aprovado;
  - **Verificado no código** — conferido na leitura do código, sem teste automatizado;
  - **Não verificado** — depende do ambiente (MySQL real, navegador) ou não pôde ser conferido.
- **Datas:** cada documento informa quando foi conferido. Se o código mudar depois disso, o documento precisa ser revisado.
- **Idioma:** português brasileiro com acentos. Mensagens copiadas do código mantêm a grafia original, que muitas vezes não tem acentos (ex.: "Comodo nao encontrado nesta casa.").

---

Conferido com o código em 08/11/2026. Resultados dos testes atualizados em 09/11/2026.
