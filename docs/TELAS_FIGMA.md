# Telas para desenhar depois no Figma

O front-end deste projeto ja serve de referencia de espacos, botoes e textos. Todas as telas sao pensadas primeiro para computador.

| Ordem | Frame no Figma | O que precisa aparecer |
| --- | --- | --- |
| 1 | Login | Logo, e-mail, senha, botao Entrar e link para cadastro |
| 2 | Cadastro | Nome, e-mail, nome da casa, senha, confirmacao, botao Criar conta |
| 3 | Painel | Menu lateral, nome da casa, resumo dos dispositivos, ambientes e atividade recente |
| 4 | Dispositivos | Lista de dispositivos com ligar/desligar, brilho, temperatura e intensidade; formulario de novo dispositivo para admin |
| 5 | Rotinas | Criar rotina com dispositivo, acao, valor, horario e dias; lista de rotinas |
| 6 | Historico | Tabela de alteracoes com data, dispositivo, acao e usuario |
| 7 | Minha casa | Lista de comodos, cadastro de comodo e moradores com permissoes |

## Conexoes do prototype

1. Login -> Painel (apos autenticar).
2. Login -> Cadastro -> Painel.
3. Menu lateral -> Painel, Dispositivos, Rotinas, Historico, Minha casa.
4. Minha casa -> Adicionar comodo / Adicionar morador / Trocar de casa.
5. Dispositivos -> Ligar / Desligar / Salvar ajuste.
6. Rotinas -> Salvar / Pausar / Ativar / Excluir.
7. Sair -> Login.

## Lo-Fi e Hi-Fi

**Lo-Fi:** faca retangulos, botoes e textos simples, sem se preocupar ainda com as cores.

**Hi-Fi:** use as cores do CSS (`--lateral`, `--azul`, `--fundo`, `--texto`), com cards arredondados, menu lateral e botoes azuis. Para evitar telas inconsistentes, use os mesmos componentes visuais em todas as paginas.

**Prototype:** ligue os botoes no Figma para mostrar o caminho do usuario. A validacao real (senha, regras e banco) fica no site, nao no Figma.
