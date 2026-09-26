# Controle de Cilindros de Oxigênio

Adaptação da base geladeira-cognvox. Manter arquitetura, auth, Docker e padrões existentes.

## Usuário
- Uma única usuária. Manter login por sessão/cookie como está.
- Desativar cadastro público: remover a rota `/auth/registro` (404/405) e a tela de registro.
- Criar script `criar_usuario.py` que cria o usuário via linha de comando.
  - `python criar_usuario.py --nome N --email E`: senha pedida no terminal (com confirmação). Recusa se já existir qualquer usuário.
  - `python criar_usuario.py --redefinir-senha --email E`: troca a senha da usuária existente. Erro se o e-mail não existir.

## Entidades
- tipos_cilindro: id (UUID), nome (único), estoque_minimo (inteiro >= 0, obrigatório), dias_alerta (padrão 30), criado_em
- lotes: id (UUID), tipo_id, quantidade (inteiro), data_vencimento, numero_lote (opcional), criado_em
  - Único por (tipo_id, data_vencimento)
- movimentacoes: id (UUID), lote_id, tipo (entrada/saida), quantidade (inteiro > 0), observacao (opcional), usuario_id, criado_em

## Regras
- Lote só nasce por entrada (não há `POST /lotes`).
- Entrada com tipo + vencimento já existente: soma na quantidade do lote. Senão, cria lote novo.
  - Se o lote existente já tem `numero_lote`, ele é mantido; só é preenchido se estiver vazio.
  - Entrada com vencimento no passado é aceita (o lote já nasce vencido).
- Saída: usuária escolhe o lote. A tela pré-seleciona o primeiro lote não vencido de menor vencimento (ou o primeiro vencido, se não houver outro). Saída de lote vencido é permitida.
- Saída maior que a quantidade do lote: bloquear (400).
- Lote com quantidade 0: some da listagem principal, continua no histórico.
- Lotes não são excluídos (não há `DELETE /lotes`).
- `PUT /lotes/{id}` edita `data_vencimento` e `numero_lote`. Se a nova data coincidir com outro lote do mesmo tipo: 409. Lote inexistente: 404.
- Erro de quantidade é corrigido com entrada/saída com observação. Não há edição de quantidade nem estorno/exclusão de movimentação.
- Tipo pode ser editado (`PUT /tipos/{id}`). Nome repetido: 409.
- Tipo só pode ser excluído se não tiver nenhum lote (mesmo zerado); caso contrário, 409.

## Alertas
- Calculados no backend; a API devolve status/flags e o frontend só exibe.
- "Hoje" é a data no fuso `America/Sao_Paulo` (configurável).
- Por lote: "vencido" se data_vencimento < hoje; "vence em breve" se faltam <= dias_alerta do tipo (inclui vencer hoje).
- Por tipo: "estoque baixo" se soma dos lotes NÃO vencidos < estoque_minimo.
- Lotes vencidos não contam como estoque disponível.

## Telas
- Estoque: tipos com estoque disponível e alertas, lotes ativos, modais de entrada, saída e editar lote.
- Tipos: cadastro, edição e exclusão de tipos.
- Histórico: todas as movimentações, sem filtros.

## Remover
- Relatório de gastos por usuário, valor_total, useGastos e página de relatório.
- Qualquer texto/nome ligado a "geladeira" no código, nomes e README (incluindo as URLs de deploy antigas). O repositório não é renomeado.
- Dados atuais não são migrados; o banco novo (`cilindros.db`) começa vazio.

## Qualidade
- Testes pytest para todas as regras acima.
- TypeScript strict sem erros.
