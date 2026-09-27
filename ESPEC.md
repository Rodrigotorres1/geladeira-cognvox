# Controle de Cilindros de Oxigênio

Adaptação da base geladeira-cognvox. Manter arquitetura, auth, Docker e padrões existentes.

## Usuário
- Uma única usuária. Manter login por sessão/cookie como está.
- Desativar cadastro público: remover a rota `/auth/registro` (404/405) e a tela de registro.
- Criar script `criar_usuario.py` que cria o usuário via linha de comando.
  - `python criar_usuario.py --nome N --email E`: senha pedida no terminal (com confirmação), de 8 a 72 caracteres (limite do bcrypt); e-mail válido. Recusa se já existir qualquer usuário.
  - `python criar_usuario.py --redefinir-senha --email E`: troca a senha da usuária existente. Erro se o e-mail não existir.
- Todas as rotas exigem sessão, exceto `POST /auth/login` e `GET /health` (verificação de saúde, responde `{"status": "ok"}`).

## Entidades
- tipos_cilindro: id (UUID), nome (único sem diferenciar maiúsculas/minúsculas; espaços nas pontas removidos; vazio ou só espaços → 422), estoque_minimo (inteiro >= 0, obrigatório), validade_anos (inteiro > 0, padrão 10 na criação), criado_em
- lotes: id (UUID), tipo_id, quantidade (inteiro), data_teste (date, sempre dia 1 do mês), data_teste_so_ano (bool), numero_lote (opcional), criado_em
  - Único por (tipo_id, data_teste, data_teste_so_ano)
  - O vencimento é do teste hidrostático, não do gás: vencimento = data_teste + validade_anos do tipo (calculado, não fica no banco).
- movimentacoes: id (UUID), lote_id, tipo (entrada/saida), quantidade (inteiro > 0), observacao (opcional), usuario_id, criado_em

## Data do teste hidrostático
- `EntradaCriar` e `LoteAtualizar` recebem `data_teste` como texto e o backend interpreta.
- Formatos aceitos: "MM/AAAA", "M/AAAA" e "AAAA".
- Só ano: data_teste = janeiro daquele ano e data_teste_so_ano = true. Por isso "2016" e "01/2016" do mesmo tipo são lotes separados.
- Mês entre 1 e 12, ano com 4 dígitos e >= 1900, e a data do teste não pode estar no futuro (mês/ano posterior ao atual). Espaços nas pontas são ignorados.
- Formato inválido: 422 com mensagem clara em português dizendo os formatos aceitos.
- A API devolve data_teste formatada como a usuária digitou ("04/2026" ou "2026"). O vencimento é sempre exibido com mês ("04/2036"; teste "2026" → vencimento "01/2036").
- Mensagens de erro exibidas à usuária em português com acentuação correta.
  - Erros de validação (422) mantêm o formato do FastAPI (`detail` como lista com `type`, `loc`, `msg`), com `msg` traduzida e prefixada pelo nome do campo (ex.: "Quantidade: deve ser maior que 0."). Traduções específicas: campo obrigatório, maior que, maior ou igual, número inteiro inválido, texto inválido, tamanho mínimo/máximo de texto e JSON inválido; demais tipos: "valor inválido". A mensagem da data do teste é mantida como está.

## Regras
- Lote só nasce por entrada (não há `POST /lotes`).
- Entrada com tipo + data do teste já existente (mesmo data_teste e data_teste_so_ano): soma na quantidade do lote. Senão, cria lote novo.
  - Se o lote existente já tem `numero_lote`, ele é mantido; só é preenchido se estiver vazio.
  - Entrada de lote já vencido é aceita.
- Saída: usuária escolhe o lote. A tela pré-seleciona o primeiro lote não vencido de menor vencimento (ou o primeiro vencido, se não houver outro). Saída de lote vencido é permitida.
- Saída maior que a quantidade do lote: bloquear (400).
- Lote com quantidade 0: some da listagem principal, continua no histórico.
- `GET /lotes` devolve os lotes ordenados por vencimento e aceita o filtro opcional `?tipo_id=`.
- Lotes não são excluídos (não há `DELETE /lotes`).
- `PUT /lotes/{id}` edita `data_teste` (texto, mesmas regras da entrada) e `numero_lote`. Se a nova data do teste coincidir com outro lote do mesmo tipo (mesmo data_teste e data_teste_so_ano): 409. Lote inexistente: 404.
- Erro de quantidade é corrigido com entrada/saída com observação. Não há edição de quantidade nem estorno/exclusão de movimentação.
- Tipo pode ser editado (`PUT /tipos/{id}`, substituição completa: nome, estoque_minimo e validade_anos obrigatórios; omitir validade_anos → 422). Nome repetido (sem diferenciar maiúsculas/minúsculas): 409. Mudar validade_anos recalcula o vencimento de todos os lotes do tipo.
- Tipo só pode ser excluído se não tiver nenhum lote (mesmo zerado); caso contrário, 409.
- Reteste: sem funcionalidade própria. O fluxo é saída do lote antigo + entrada com a nova data de teste.

## Alertas
- Calculados no backend; a API devolve status/flags e o frontend só exibe.
- "Hoje" é a data no fuso `America/Sao_Paulo`, configurável pela variável `TIMEZONE`.
- Por lote: meses_restantes = (ano_venc*12 + mes_venc) - (ano_hoje*12 + mes_hoje)
  - < 0: "vencido"; <= 2: "urgente"; <= 6: "atencao"; senão "ok".
  - Os limites (6 e 2) ficam em Settings, configuráveis pelas variáveis `MESES_ALERTA_ATENCAO` e `MESES_ALERTA_URGENTE`.
  - A API devolve por lote `status` e `meses_restantes` (usado na tela para "vence em X meses", "vence este mês" ou "vencido há X meses"; acima de 12 meses, em anos e meses).
  - O cilindro pode ser usado até o fim do mês de vencimento (meses_restantes = 0 ainda não é vencido).
  - Lote com só ano vence em janeiro do ano de vencimento (ex.: teste "2016" → vencimento "01/2026").
- Por tipo: "estoque baixo" se soma dos lotes NÃO vencidos < estoque_minimo.
- Lotes vencidos não contam como estoque disponível.

## Telas
- Layout responsivo, pensado para uso no celular.
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
