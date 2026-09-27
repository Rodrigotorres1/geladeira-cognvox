# Controle de Cilindros de Oxigênio

## 1. Sobre o projeto

Aplicação full stack para controlar o estoque de cilindros de oxigênio de **uma única usuária**: quais cilindros existem, quando cada lote precisa de novo teste hidrostático e quais tipos estão abaixo do estoque mínimo. A tela foi pensada para uso no celular.

```
/backend   # API em FastAPI + SQLAlchemy + SQLite
/frontend  # Aplicação Vite + React + TypeScript + Tailwind
```

- **Backend**: autenticação por sessão (cookie `HttpOnly`), cadastro de tipos de cilindro, lotes identificados pela data do teste hidrostático, movimentações de entrada/saída com histórico e cálculo dos alertas.
- **Frontend**: login, estoque por tipo com alertas, registro de entrada/saída, edição de lote, cadastro de tipos e histórico de movimentações.

Não existe cadastro público: a usuária é criada pelo script `backend/criar_usuario.py` (seção 2).

A especificação funcional completa está em [`ESPEC.md`](ESPEC.md).

---

## 2. Como rodar o backend

```powershell
cd backend
python -m venv venv                   # se o venv ainda não existir
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env                # depois ajuste os valores, veja a seção 4
python criar_usuario.py --nome "Maria" --email maria@exemplo.com
uvicorn main:app --reload --port 8000
```

Com o servidor rodando:
- `http://localhost:8000/health` retorna `{"status": "ok"}`
- `http://localhost:8000/docs` abre a documentação interativa (Swagger), onde dá para testar todas as rotas, inclusive o login (o cookie fica no próprio navegador)

As tabelas do banco (SQLite, arquivo `cilindros.db`) são criadas automaticamente na primeira vez que o servidor sobe (ou que o `criar_usuario.py` roda).

### Criando a usuária

```powershell
python criar_usuario.py --nome "Maria" --email maria@exemplo.com
python criar_usuario.py --redefinir-senha --email maria@exemplo.com
```

- A senha é sempre pedida no terminal, com confirmação — nunca por argumento, para não ficar no histórico do shell. Mínimo de 8 e máximo de 72 caracteres.
- Criar é recusado se já existir **qualquer** usuário (o sistema tem uma única usuária). Para trocar a senha, use `--redefinir-senha`.

### Rodando os testes

```powershell
cd backend
pytest -v
```

Os testes (`backend/tests/`) rodam contra um SQLite isolado (`tests/test.db`, criado e apagado automaticamente) — nunca tocam em `cilindros.db`. Cobrem autenticação e sessão (logout, expiração, cookie adulterado), o script de usuária, as mensagens de validação em português, tipos, lotes, movimentações, a interpretação da data do teste e as bordas dos alertas (com a data de "hoje" fixada).

---

## 3. Como rodar o frontend

```powershell
cd frontend
npm install
npm run dev
```

Abre em `http://localhost:5173`. O backend precisa estar rodando em `http://localhost:8000` (seção 2) — o `FRONTEND_ORIGIN` do `.env` do backend já vem configurado para `http://localhost:5173`, então CORS com cookies funciona sem ajuste extra.

Verificações usadas no projeto: `npx tsc -b` (TypeScript strict) e `npm run lint` (oxlint).

**Sobre a URL da API:** vem de `VITE_API_URL` (seção 4), lida em [`frontend/src/api/client.ts`](frontend/src/api/client.ts). Sem essa variável, cai no fallback `http://localhost:8000` — por isso `npm run dev` funciona direto, sem criar nenhum `.env` local.

---

## 4. Variáveis de ambiente

### Backend (`backend/.env`, a partir de `backend/.env.example`)

| Variável | Obrigatória | Exemplo | Descrição |
|---|---|---|---|
| `DATABASE_URL` | Sim | `sqlite:///./cilindros.db` | String de conexão do banco (SQLite por padrão; uma URL do Postgres também funciona, já que o SQLAlchemy abstrai o driver) |
| `SECRET_KEY` | Sim | `troque-por-um-valor-aleatorio-longo` | Chave que assina o cookie de sessão (`itsdangerous`). Deve ser aleatória e secreta em produção |
| `FRONTEND_ORIGIN` | Sim | `http://localhost:5173` | Origem permitida no CORS; precisa bater exatamente com a URL do frontend para os cookies de sessão funcionarem |
| `ENVIRONMENT` | Não (default `local`) | `local` | `local` desliga o `Secure` do cookie (funciona em `http://`); qualquer outro valor (ex.: `production`) liga `Secure=True` e `SameSite=None` |
| `TIMEZONE` | Não (default `America/Sao_Paulo`) | `America/Sao_Paulo` | Fuso usado para decidir o que é "hoje" nos alertas e na validação de data futura |
| `MESES_ALERTA_ATENCAO` | Não (default `6`) | `6` | Até quantos meses do vencimento o lote fica em "atenção" |
| `MESES_ALERTA_URGENTE` | Não (default `2`) | `2` | Até quantos meses do vencimento o lote fica "urgente" |

`SECRET_KEY` e `DATABASE_URL` nunca são commitados — só `.env.example` fica versionado; `.env` está no `.gitignore`.

### Frontend (`frontend/.env`, a partir de `frontend/.env.example`)

| Variável | Obrigatória | Exemplo | Descrição |
|---|---|---|---|
| `VITE_API_URL` | Não (default `http://localhost:8000`) | `https://api.exemplo.com` | URL base do backend. Em local pode ficar sem definir; em produção precisa apontar para o backend real |

---

## 5. Regras de negócio

### Tipos, lotes e movimentações

- **Tipo de cilindro**: nome (único sem diferenciar maiúsculas/minúsculas; espaços nas pontas são removidos), estoque mínimo e validade do teste hidrostático em anos (padrão 10 na criação; obrigatória no `PUT`).
- **Lote**: cilindros de um tipo com a mesma data de teste hidrostático. O vencimento **não é do gás, é do teste**: vencimento = data do teste + validade do tipo. Ele é calculado, não fica gravado — mudar a validade de um tipo recalcula o vencimento de todos os lotes dele.
- **Movimentação**: toda entrada e saída fica registrada (quantidade, observação opcional, quem fez e quando). É o histórico.

### Data do teste

A data do teste é enviada como **texto** e interpretada pelo backend:

| Digitado | Guardado como | Exibido | Vencimento (validade 10 anos) |
|---|---|---|---|
| `04/2016` ou `4/2016` | abril/2016 | `04/2016` | `04/2026` |
| `2016` | janeiro/2016, marcado como "só ano" | `2016` | `01/2026` |

- Mês de 1 a 12, ano com 4 dígitos e sem data no futuro. Fora disso: `422` com mensagem em português dizendo os formatos aceitos.
- "Só ano" assume janeiro — a leitura mais conservadora (vence antes). O vencimento é sempre exibido com mês, para não parecer que vale o ano inteiro.
- `2016` e `01/2016` do mesmo tipo são **lotes diferentes** (a unicidade é tipo + data do teste + "só ano").

### Entrada, saída e edição

- **Entrada** com tipo e data do teste que já existem soma no lote; senão cria um lote novo. O número do lote original é mantido (só é preenchido se estiver vazio).
- **Saída**: a usuária escolhe o lote; a tela já vem com o lote não vencido que vence primeiro (ou, se só houver lotes vencidos, com o primeiro deles). Saída maior que a quantidade do lote é bloqueada (`400`). Saída de lote vencido é permitida.
- **Lote zerado** some da tela de estoque, mas continua no histórico.
- **Lotes não são excluídos.** `PUT /lotes/{id}` corrige a data do teste e o número do lote (`409` se a nova data colidir com outro lote do mesmo tipo). Erro de quantidade se corrige com uma entrada/saída com observação.
- **Tipo** só pode ser excluído se não tiver nenhum lote, nem zerado (`409`).
- **Reteste** não tem funcionalidade própria: é uma saída do lote antigo e uma entrada com a nova data de teste.

### Alertas (calculados no backend)

`meses_restantes = (ano_venc × 12 + mês_venc) − (ano_hoje × 12 + mês_hoje)`

| `meses_restantes` | Status | Na tela |
|---|---|---|
| menor que 0 | `vencido` | badge vermelho |
| 0 a 2 | `urgente` | badge laranja |
| 3 a 6 | `atencao` | badge amarelo |
| mais de 6 | `ok` | sem badge |

- O cilindro pode ser usado até o fim do mês de vencimento (`meses_restantes = 0` ainda é "urgente", não "vencido").
- **Estoque disponível** de um tipo é a soma dos lotes **não vencidos**; o tipo fica com **estoque baixo** quando esse total é menor que o estoque mínimo.
- Os limites 6 e 2 são configuráveis (seção 4).

---

## 6. Rotas da API

Todas as rotas, exceto `/auth/login` e `/health`, exigem sessão válida via cookie `session_id` — sem ele, respondem `401 Unauthorized`.

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Autentica e define o cookie de sessão |
| POST | `/auth/logout` | Invalida a sessão e remove o cookie |
| GET | `/auth/me` | Dados da usuária autenticada |
| GET | `/tipos` | Lista os tipos com estoque disponível e alerta de estoque baixo |
| POST | `/tipos` | Cria um tipo |
| PUT | `/tipos/{id}` | Atualiza um tipo (substituição completa: `nome`, `estoque_minimo` e `validade_anos` obrigatórios) |
| DELETE | `/tipos/{id}` | Exclui um tipo (bloqueado se tiver lotes) |
| GET | `/lotes?tipo_id=` | Lotes com estoque, ordenados por vencimento, com status (filtro por tipo opcional) |
| PUT | `/lotes/{id}` | Corrige data do teste e número do lote |
| POST | `/movimentacoes/entrada` | Registra entrada (soma no lote existente ou cria outro) |
| POST | `/movimentacoes/saida` | Registra saída de um lote |
| GET | `/movimentacoes` | Histórico, do mais recente para o mais antigo |

Não existem `POST /auth/registro`, `POST /lotes` nem `DELETE /lotes/{id}` (seção 5).

**Erros de validação (`422`)** vêm no formato padrão do FastAPI — `{"detail": [{"type", "loc", "msg", ...}]}` —, mas com `msg` em português e com o nome do campo, ex.: `"Quantidade: deve ser maior que 0."`, `"Estoque mínimo: campo obrigatório."`, `"Nome: não pode ficar em branco."`. A tradução fica em `backend/app/core/validacao.py`; tipos de erro sem tradução específica recebem `"<Campo>: valor inválido."`. As mensagens da data do teste já nascem em português e passam como estão.

> **Nota sobre `curl` no Windows:** no PowerShell, `curl` é apelido de `Invoke-WebRequest` e não aceita `-c`/`-b`/`-d`. Os exemplos abaixo usam o `curl` real (Git Bash/WSL/Linux/macOS, ou `curl.exe` no Windows). Em PowerShell nativo, use `Invoke-RestMethod -SessionVariable session` no login e `-WebSession $session` nas chamadas seguintes.

### Autenticação

```bash
curl -c cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "maria@exemplo.com", "senha": "senha1234"}'
```
```json
// 200 OK
{"id": "6752139c-5355-4c61-b942-be0f719f7e4b", "nome": "Maria", "email": "maria@exemplo.com", "criado_em": "2026-09-26T22:28:19.150249"}
```
`-c cookies.txt` salva o cookie `session_id`; as próximas chamadas usam `-b cookies.txt`. Erro: `401` (`"E-mail ou senha inválidos"`).

`POST /auth/logout` responde `204` e apaga a sessão no banco; depois disso `/auth/me` volta a responder `401`.

### Tipos

```bash
curl -b cookies.txt -X POST http://localhost:8000/tipos \
  -H "Content-Type: application/json" \
  -d '{"nome": "Cilindro 10L", "estoque_minimo": 3}'
```
```json
// 201 Created — validade_anos é opcional (padrão 10)
{"id": "cae9f7c3-ad8f-4699-a4b5-de567277fb93", "nome": "Cilindro 10L", "estoque_minimo": 3, "validade_anos": 10, "criado_em": "2026-09-26T22:28:19.445480", "estoque_disponivel": 0, "estoque_baixo": true}
```
Erros: `409` se já existe um tipo com esse nome, sem diferenciar maiúsculas/minúsculas; `422` se o nome estiver vazio (ou só com espaços), se `estoque_minimo` for negativo ou se `validade_anos` não for maior que zero. No `PUT`, omitir `validade_anos` também dá `422` — não volta para o padrão em silêncio. `DELETE /tipos/{id}` com lotes: `409` (`"Não é possível excluir um tipo que já tem lotes registrados"`).

### Entrada

```bash
curl -b cookies.txt -X POST http://localhost:8000/movimentacoes/entrada \
  -H "Content-Type: application/json" \
  -d '{"tipo_id": "cae9f7c3-ad8f-4699-a4b5-de567277fb93", "data_teste": "04/2016", "quantidade": 2, "numero_lote": "A-17", "observacao": "Compra"}'
```
```json
// 201 Created
{"id": "c0dc1f13-fa5b-49d5-a4a6-f2a7e14021c3", "lote": {"id": "cf647e92-4f3f-46ce-84fb-a94dc044c40f", "tipo": {"id": "cae9f7c3-ad8f-4699-a4b5-de567277fb93", "nome": "Cilindro 10L"}, "data_teste": "04/2016", "vencimento": "04/2026", "numero_lote": "A-17"}, "usuario_id": "6752139c-5355-4c61-b942-be0f719f7e4b", "tipo": "entrada", "quantidade": 2, "observacao": "Compra", "criado_em": "2026-09-26T22:28:19.497049"}
```
`numero_lote` e `observacao` são opcionais. Erros: `404` se o tipo não existir; `422` se a data do teste for inválida:
```json
// 422 Unprocessable Entity
{"detail": [{"type": "data_teste_invalida", "loc": ["body", "data_teste"], "msg": "Data do teste inválida. Use MM/AAAA, M/AAAA ou AAAA (ex.: 04/2016, 4/2016 ou 2016).", "input": "04/26"}]}
```

### Lotes

```bash
curl -b cookies.txt http://localhost:8000/lotes
```
```json
// 200 OK — ordenados por vencimento; só lotes com quantidade > 0
[
  {"id": "cf647e92-4f3f-46ce-84fb-a94dc044c40f", "tipo": {"id": "cae9f7c3-ad8f-4699-a4b5-de567277fb93", "nome": "Cilindro 10L"}, "quantidade": 2, "data_teste": "04/2016", "vencimento": "04/2026", "numero_lote": "A-17", "criado_em": "2026-09-26T22:28:19.492488", "meses_restantes": -5, "status": "vencido"},
  {"id": "746ae7a7-1f8f-4db3-8774-3e8488c7234b", "tipo": {"id": "cae9f7c3-ad8f-4699-a4b5-de567277fb93", "nome": "Cilindro 10L"}, "quantidade": 5, "data_teste": "2021", "vencimento": "01/2031", "numero_lote": null, "criado_em": "2026-09-26T22:28:19.511591", "meses_restantes": 52, "status": "ok"}
]
```

```bash
curl -b cookies.txt -X PUT http://localhost:8000/lotes/cf647e92-4f3f-46ce-84fb-a94dc044c40f \
  -H "Content-Type: application/json" \
  -d '{"data_teste": "05/2016", "numero_lote": "A-17"}'
```
`200` com o lote atualizado (mesmo formato do `GET /lotes`). Erros: `404` se o lote não existir; `409` (`"Já existe outro lote desse tipo com essa data de teste"`); `422` se a data for inválida.

### Saída e histórico

```bash
curl -b cookies.txt -X POST http://localhost:8000/movimentacoes/saida \
  -H "Content-Type: application/json" \
  -d '{"lote_id": "cf647e92-4f3f-46ce-84fb-a94dc044c40f", "quantidade": 1, "observacao": "Paciente"}'
```
`201` com a movimentação (mesmo formato da entrada). Erros: `404` se o lote não existir; `400` (`"Quantidade maior que a disponível no lote"`).

`GET /movimentacoes` devolve a lista de movimentações nesse mesmo formato, da mais recente para a mais antiga, incluindo as de lotes já zerados.

---

## 7. Decisões técnicas

### Por que UUID como chave primária

Todas as chaves primárias são UUID v4 gerados no backend, nunca IDs sequenciais. Um ID incremental permite tentar adivinhar registros só variando o número na URL (`/lotes/1`, `/lotes/2`...) — IDOR/enumeração de recursos. Um UUID v4 não tem "próximo" previsível.

### Como funciona a sessão via cookie HttpOnly

1. `POST /auth/login` valida e-mail/senha e cria uma linha na tabela `sessoes` (expira em 7 dias).
2. O `id` dessa sessão é assinado com `itsdangerous` (usando `SECRET_KEY`) e devolvido no cookie `session_id` com `HttpOnly=True`. Em `local`: `SameSite=Lax`, sem `Secure`. Fora de `local`: `SameSite=None` com `Secure=True` — necessário quando frontend e backend ficam em domínios diferentes (cross-site).
3. Em toda rota protegida, o backend confere a assinatura e verifica no banco se a sessão existe e não expirou. Por isso o frontend usa `withCredentials: true` e o CORS precisa de `allow_credentials=True` com origem explícita.
4. `POST /auth/logout` apaga a sessão no banco — ela morre no servidor, não só no navegador.

Cookie `HttpOnly` em vez de token em `localStorage`: um XSS não consegue ler o cookie. Sessão no banco em vez de JWT autocontido: dá para revogar a qualquer momento. A senha é guardada só como hash bcrypt (`passlib`).

### Arquitetura em camadas

- **Backend:** `routers` só validam a requisição (via `schemas`) e traduzem erros para HTTP; `services` concentram as regras de negócio, sem depender de HTTP; `models` descrevem a persistência, separados dos `schemas` (contrato da API).
- **Regras puras isoladas:** `services/data_teste.py` (interpretar/formatar a data do teste, calcular vencimento) e `services/alertas.py` (meses restantes, status, estoque disponível) recebem "hoje" como parâmetro — os testes fixam a data e cobrem as bordas sem depender do relógio.
- **Frontend:** `pages` decidem o que aparece na tela, `hooks` decidem de onde vêm os dados (nenhuma página chama `axios` direto), `components` guardam os modais e peças de UI reaproveitadas.

### Escolhas de stack

- **FastAPI + SQLAlchemy + SQLite:** validação e documentação automáticas a partir dos schemas Pydantic (Swagger em `/docs`), ORM com o modelo versionado em código. SQLite basta para o volume de uma única usuária; trocar para Postgres é só mudar `DATABASE_URL`.
- **Vite + React + TypeScript + Tailwind:** TypeScript strict pega mudanças de contrato da API em tempo de compilação; Tailwind facilita o layout responsivo (mobile first).

---

## 8. Decisões e trade-offs conscientes

| Trade-off | Por que ficou assim | Como resolver se precisar |
|---|---|---|
| **Sem migrations (Alembic)** | O schema é criado com `create_all`, que não altera tabelas existentes. Com um banco novo (`cilindros.db`) isso basta. | Adotar Alembic antes da primeira mudança de schema com dados reais em produção. |
| **Sem rate limiting em `/auth/login`** | Não há limite de tentativas de senha. | Middleware de rate limiting (ex.: `slowapi`) por IP e e-mail, ou bloqueio temporário após N falhas. |
| **Sem limpeza de sessões expiradas** | Sessão expirada já é tratada como não autenticada, mas a linha fica na tabela `sessoes`. | Job periódico apagando sessões expiradas, ou limpar as da usuária a cada login. |
| **Sem lock na checagem de estoque da saída** | A saída lê a quantidade do lote e depois grava. Com uma única usuária e SQLite, duas saídas simultâneas do mesmo lote são improváveis. | Em Postgres, `SELECT ... FOR UPDATE` na linha do lote ou `CHECK (quantidade >= 0)` no banco. |
| **Datas de criação em UTC sem fuso** | `criado_em` é gravado em UTC sem tzinfo (`app/core/tempo.py:agora_utc`), porque o SQLite não guarda fuso; o frontend converte para o horário local ao exibir. | Migrar para datetimes com fuso (`datetime.now(UTC)`). |
| **Sem testes automatizados no frontend** | O projeto não tem runner de testes no frontend (Vitest/Testing Library). As regras de negócio estão no backend e cobertas por pytest, mas o que é só de tela fica sem teste automatizado: pré-seleção do lote na saída, preenchimento dos modais, texto "vence em X anos e Y meses", badges e layout no celular. A verificação hoje é `npx tsc -b`, `npm run lint` e uso manual. | Adicionar Vitest + Testing Library para as funções de `lib/` (`loteParaSaida`, `descreverMesesRestantes`, `extrairMensagemErro`) e para os modais; Playwright para o fluxo completo em viewport de celular. |
| **Imagens Docker sem hot-reload** | As imagens copiam o código no build, então cada mudança exige `docker compose up --build`. | Montar o código como bind mount e manter `--reload`/HMR ativos. |

---

## 9. Como rodar com Docker Compose

```powershell
copy backend\.env.example backend\.env    # se ainda não existir — o compose lê esse arquivo
docker compose up --build
docker compose exec backend python criar_usuario.py --nome "Maria" --email maria@exemplo.com
```

- Backend em `http://localhost:8000` (`/docs` para o Swagger); frontend em `http://localhost:5173`.
- `docker compose down` remove os containers, mas os dados continuam no volume nomeado `backend_data`; `docker compose down -v` apaga o volume também.
- O `criar_usuario.py` roda dentro do container (`exec`), então grava no mesmo banco que a API usa.

**O que cada `Dockerfile` faz:**

- **`backend/Dockerfile`**: `python:3.13-slim`, instala o `requirements.txt` (inclui `tzdata`, necessário para o fuso `America/Sao_Paulo`), copia o código e sobe `uvicorn main:app --host 0.0.0.0 --port 8000`. O `--host 0.0.0.0` é obrigatório — sem ele o uvicorn só aceita conexões de dentro do próprio container.
- **`frontend/Dockerfile`**: `node:22-slim`, instala as dependências com `npm ci` e sobe `npm run dev -- --host 0.0.0.0`, pelo mesmo motivo.

**Como os dois serviços se comunicam:** eles **não conversam pela rede interna do Docker**. Quem fala com o backend é o navegador, na máquina host; o frontend é só uma SPA que o navegador baixa. Por isso `src/api/client.ts` aponta para `http://localhost:8000` mesmo no Docker: com `ports: "8000:8000"`, o backend fica acessível em `localhost:8000` a partir do host. `http://backend:8000` só resolveria para outros containers, não para o navegador.

**Persistência do banco:** o `docker-compose.yml` sobrescreve `DATABASE_URL` para `sqlite:///./data/cilindros.db` e monta o volume nomeado `backend_data` em `/app/data`, separando o ciclo de vida dos dados do ciclo de vida do container. O `.dockerignore` exclui qualquer `*.db` local, então a imagem nunca leva dados junto.
