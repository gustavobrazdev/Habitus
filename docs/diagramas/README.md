# Diagramas do Habitus

Esta pasta reúne os diagramas UML de casos de uso e de sequência e o diagrama da organização dos testes. Ela também serve de mapa para os diagramas que já existiam na documentação: eles continuam nos documentos originais e aparecem aqui apenas como links.

- Índice da documentação técnica: [docs/README.md](../README.md).
- Visão geral do projeto: [README principal](../../README.md).
- Em caso de divergência entre qualquer diagrama e o código, **o código prevalece**.

Todos os diagramas usam [Mermaid](https://mermaid.js.org/), que o GitHub desenha diretamente a partir do texto do arquivo `.md`.

## Diagramas desta pasta

| Documento | Tipo de diagrama | O que mostra |
| --- | --- | --- |
| [CASOS_DE_USO.md](CASOS_DE_USO.md) | UML de casos de uso (fluxograma Mermaid com a notação da UML) | Os atores Visitante, MORADOR (`comum`), ADMIN (`administrador`) e o Executor de rotinas, os casos de uso implementados, as relações «include», «extend» e de generalização, e a rastreabilidade até rotas, permissões e testes |
| [SEQUENCIA_TRANSFERIR_DISPOSITIVO.md](SEQUENCIA_TRANSFERIR_DISPOSITIVO.md) | UML de sequência | A transferência de um dispositivo entre cômodos, do formulário até o MySQL: verificações globais, permissão, validação, serviço, transação, repositórios, COMMIT e ROLLBACK |
| [ORGANIZACAO_TESTES.md](ORGANIZACAO_TESTES.md) | Fluxogramas e gráfico de pizza | Os 144 testes coletados, os grupos e as categorias, a distribuição por arquivo, os componentes verificados por cada arquivo e as lacunas de cobertura |

## Diagramas que já existiam

| Diagrama | Tipo Mermaid | Onde está |
| --- | --- | --- |
| Camadas do back-end | `flowchart` | [README principal, Arquitetura](../../README.md#arquitetura) |
| Relacionamento entre as tabelas (resumo) | `erDiagram` | [README principal, Banco de dados](../../README.md#banco-de-dados) |
| Hierarquia dos dispositivos (resumo) | `classDiagram` | [README principal, Programação Orientada a Objetos](../../README.md#programação-orientada-a-objetos) |
| Agendador com `heapq` e `deque` (resumo) | `flowchart` | [README principal, Estruturas de Dados](../../README.md#estruturas-de-dados) |
| Os dois processos e o banco | `flowchart` | [ARQUITETURA.md, seção 1](../ARQUITETURA.md#1-visão-geral-da-execução) |
| Dependências reais entre os módulos | `flowchart` | [ARQUITETURA.md, seção 2.2](../ARQUITETURA.md#22-dependências-reais-entre-os-módulos) |
| Sequência: ajustar o brilho de uma luz (AJAX) | `sequenceDiagram` | [ARQUITETURA.md, seção 4.2](../ARQUITETURA.md#42-exemplo-completo-ajustar-o-brilho-de-uma-luz) |
| Fluxo do login | `flowchart` | [AUTENTICACAO_E_SEGURANCA.md, seção 3.1](../AUTENTICACAO_E_SEGURANCA.md#31-login) |
| Modelo entidade-relacionamento completo | `erDiagram` | [BANCO_DE_DADOS.md, seção 2](../BANCO_DE_DADOS.md#2-diagrama-entidade-relacionamento) |
| Escolha entre `schema.sql` e as migrações | `flowchart` | [BANCO_DE_DADOS.md, seção 9.2](../BANCO_DE_DADOS.md#92-como-saber-o-que-falta) |
| Hierarquia dos dispositivos | `classDiagram` | [ESTRUTURAS_E_POO.md, seção 2.1](../ESTRUTURAS_E_POO.md#21-hierarquia-dos-dispositivos) |
| Demais classes do domínio | `classDiagram` | [ESTRUTURAS_E_POO.md, seção 2.2](../ESTRUTURAS_E_POO.md#22-demais-classes-do-domínio) |
| Agendamento passo a passo | `flowchart` | [ESTRUTURAS_E_POO.md, seção 13](../ESTRUTURAS_E_POO.md#13-agendamento-passo-a-passo) |
| Sequência: executor de rotinas | `sequenceDiagram` | [EXECUTOR_ROTINAS.md, seção 5.1](../EXECUTOR_ROTINAS.md#51-diagrama-do-executor) |
| Verificação do vínculo com a casa | `flowchart` | [ROTAS_E_PERMISSOES.md, seção 4.4](../ROTAS_E_PERMISSOES.md#44-como-o-vínculo-com-a-casa-é-verificado) |

São 15 diagramas: os 4 do README principal são versões resumidas, e os 11 de `docs/` são as versões completas de cada assunto.

## Ordem de leitura sugerida

1. [CASOS_DE_USO.md](CASOS_DE_USO.md): o que o sistema faz e quem pode fazer.
2. [SEQUENCIA_TRANSFERIR_DISPOSITIVO.md](SEQUENCIA_TRANSFERIR_DISPOSITIVO.md): como uma operação atravessa as camadas.
3. [ORGANIZACAO_TESTES.md](ORGANIZACAO_TESTES.md): como esse comportamento é verificado.

---

Criado em 11/11/2026.
