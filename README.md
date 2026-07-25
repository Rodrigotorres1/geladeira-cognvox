# Sistema de Controle de Estoque de Geladeira

## 1. Sobre o projeto

Aplicação full stack para controle de estoque de uma **geladeira compartilhada** entre colaboradores: cada pessoa cadastra e consome itens, e o sistema mantém o controle de quanto foi comprado, quanto foi consumido e **quanto cada usuário gastou** ao longo do tempo — sem depender de planilha ou de alguém lembrar de anotar manualmente.

```
/backend   # API em FastAPI + SQLAlchemy + SQLite
/frontend  # Aplicação Vite + React + TypeScript
```

- **Backend**: autenticação por sessão (cookie `HttpOnly`), CRUD de itens, registro de movimentações (entrada/saída) e relatório de gastos por período.
- **Frontend**: login/cadastro, listagem e gestão do estoque, registro de consumo e visualização dos gastos (com gráfico).

Duas formas de rodar: backend e frontend separados (seções 2 e 3), ou tudo de uma vez com `docker compose up --build` (seção 8).

---

## 2. Como rodar o backend

```powershell
cd backend
python -m venv venv                   # se o venv ainda não existir
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env                # depois ajuste os valores, veja a secao 4
uvicorn main:app --reload --port 8000
```

Com o servidor rodando:
- `http://localhost:8000/health` retorna `{"status": "ok"}`
- `http://localhost:8000/docs` abre a documentação interativa (Swagger) gerada automaticamente pelo FastAPI — dá para testar todas as rotas por lá, inclusive o fluxo de login (o cookie é guardado pelo próprio navegador)

As tabelas do banco (SQLite, arquivo `geladeira.db`) são criadas automaticamente na primeira vez que o servidor sobe.

### Rodando os testes

```powershell
cd backend
pytest -v
```

Os 11 testes (`backend/tests/`) rodam contra um SQLite isolado (`tests/test.db`, criado e apagado automaticamente) — nunca tocam em `geladeira.db`, o banco de desenvolvimento.

---

## 3. Como rodar o frontend

```powershell
cd frontend
npm install
npm run dev
```

Abre em `http://localhost:5173`. O backend precisa estar rodando em `http://localhost:8000` (seção 2) — o `FRONTEND_ORIGIN` do `.env` do backend já vem configurado para `http://localhost:5173` por padrão, então CORS com cookies funciona sem ajuste extra.

**Sobre a URL da API:** o frontend não tem variável de ambiente hoje — a URL do backend é fixa em [`frontend/src/api/client.ts`](frontend/src/api/client.ts) (`http://localhost:8000`), porque o projeto roda inteiro em local. Numa aplicação real isso viraria uma env var (`VITE_API_URL`, lida via `import.meta.env`) para apontar para um backend diferente em cada ambiente de deploy — ver seção 7.

---

## 4. Variáveis de ambiente

### Backend (`backend/.env`, a partir de `backend/.env.example`)

| Variável | Obrigatória | Exemplo | Descrição |
|---|---|---|---|
| `DATABASE_URL` | Sim | `sqlite:///./geladeira.db` | String de conexão do banco (SQLite por padrão; uma URL do Postgres também funciona, já que o SQLAlchemy abstrai o driver) |
| `SECRET_KEY` | Sim | `troque-por-um-valor-aleatorio-longo` | Chave usada para assinar o cookie de sessão (`itsdangerous`); sem ela a aplicação recusa subir. Deve ser um valor aleatório e secreto em produção |
| `FRONTEND_ORIGIN` | Sim | `http://localhost:5173` | Origem permitida no CORS; precisa bater exatamente com a URL do frontend para os cookies de sessão funcionarem |
| `ENVIRONMENT` | Não (default `local`) | `local` | `local` desliga o `Secure` do cookie (funciona em `http://`); qualquer outro valor (ex.: `production`) liga `Secure=True`, exigindo HTTPS |

`SECRET_KEY` e `DATABASE_URL` nunca são commitados — só `.env.example` (com valores de exemplo/placeholder) fica versionado; `.env` está no `.gitignore`.

### Frontend

Não há `.env` no frontend hoje. A única configuração externa (URL do backend) está hardcoded em `src/api/client.ts` — ver nota na seção 3 e o trade-off na seção 7.

---

## 5. Rotas da API implementadas

Todas as rotas (exceto `/auth/registro` e `/auth/login`) exigem sessão válida via cookie `session_id` — sem ele, respondem `401 Unauthorized`.

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| POST | `/auth/registro` | Não | Cria um novo usuário |
| POST | `/auth/login` | Não | Autentica e define o cookie de sessão |
| POST | `/auth/logout` | Sim | Invalida a sessão e remove o cookie |
| GET | `/auth/me` | Sim | Retorna os dados do usuário autenticado |
| GET | `/itens` | Sim | Lista todos os itens do estoque (geladeira compartilhada) |
| POST | `/itens` | Sim | Cria um item, vinculado ao usuário autenticado |
| PUT | `/itens/{id}` | Sim | Atualiza um item existente (substituição completa) |
| DELETE | `/itens/{id}` | Sim | Remove um item (bloqueado se houver movimentações) |
| POST | `/movimentacoes` | Sim | Registra uma entrada (reposição) ou saída (consumo) |
| GET | `/relatorios/gastos` | Sim | Total gasto pelo usuário autenticado num período |

> **Nota sobre `curl` no Windows:** dentro do PowerShell, `curl` é apelido de `Invoke-WebRequest` e não aceita as flags `-c`/`-b`/`-d` do curl real. Os exemplos abaixo usam `curl` (Git Bash/WSL/Linux/macOS, ou `curl.exe` explícito no Windows). Em PowerShell nativo, troque por `Invoke-RestMethod -SessionVariable session` (login) e `-WebSession $session` (chamadas seguintes) — exemplo completo logo após `/auth/login`.

### Autenticação

**POST /auth/registro**

```bash
curl -X POST http://localhost:8000/auth/registro \
  -H "Content-Type: application/json" \
  -d '{"nome": "Rodrigo", "email": "rodrigo@teste.com", "senha": "senha1234"}'
```
```json
// 201 Created
{"id": "5eabe54b-3a06-4089-8e95-584185758bd4", "nome": "Rodrigo", "email": "rodrigo@teste.com", "criado_em": "2026-07-24T17:34:04.749696"}
```
Erros: `409 Conflict` se o e-mail já existe. `422 Unprocessable Entity` se a senha tiver menos de 8 ou mais de 72 caracteres (limite do bcrypt), ou o e-mail for inválido.

**POST /auth/login**

```bash
curl -c cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "rodrigo@teste.com", "senha": "senha1234"}'
```
`-c cookies.txt` salva o cookie `session_id` recebido; as próximas chamadas usam `-b cookies.txt` para reenviá-lo.
```json
// 200 OK — mesmo formato do registro
{"id": "5eabe54b-3a06-4089-8e95-584185758bd4", "nome": "Rodrigo", "email": "rodrigo@teste.com", "criado_em": "2026-07-24T17:34:04.749696"}
```
Erro: `401 Unauthorized` se e-mail/senha não conferirem.

```powershell
# Equivalente em PowerShell (mesma logica vale para as demais rotas abaixo,
# so trocando -Method/-Body/URI):
$resp = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method Post `
  -ContentType "application/json" `
  -Body '{"email": "rodrigo@teste.com", "senha": "senha1234"}' `
  -SessionVariable session
```

**GET /auth/me**

```bash
curl -b cookies.txt http://localhost:8000/auth/me
```
```json
// 200 OK
{"id": "5eabe54b-3a06-4089-8e95-584185758bd4", "nome": "Rodrigo", "email": "rodrigo@teste.com", "criado_em": "2026-07-24T17:34:04.749696"}
```
Erro: `401 Unauthorized` sem cookie válido.

**POST /auth/logout**

```bash
curl -b cookies.txt -c cookies.txt -X POST http://localhost:8000/auth/logout
```
`204 No Content` (sem corpo). Depois disso, `/auth/me` volta a responder `401`.

### Itens do estoque

A geladeira é compartilhada: `GET /itens` lista os itens de todos os usuários; `POST /itens` vincula o item criado ao usuário autenticado (`usuario_id`), mas qualquer usuário logado pode editar (`PUT`) ou remover (`DELETE`) qualquer item.

**POST /itens**

```bash
curl -b cookies.txt -X POST http://localhost:8000/itens \
  -H "Content-Type: application/json" \
  -d '{"nome": "Leite", "quantidade": 2, "unidade": "litro", "valor_unitario": 5.50, "validade": "2026-08-01"}'
```
```json
// 201 Created
{"id": "023aaf93-ff91-4471-8ce9-66298ecfa495", "usuario_id": "c8a21794-030b-4f9c-978b-65838740f751", "nome": "Leite", "quantidade": 2.0, "unidade": "litro", "valor_unitario": "5.50", "validade": "2026-08-01", "atualizado_em": "2026-07-24T21:00:38.898690"}
```
`validade` é opcional. Erro: `422 Unprocessable Entity` se `quantidade` ou `valor_unitario` forem negativos.

**GET /itens**

```bash
curl -b cookies.txt http://localhost:8000/itens
```
```json
// 200 OK
[
  {"id": "023aaf93-ff91-4471-8ce9-66298ecfa495", "usuario_id": "c8a21794-030b-4f9c-978b-65838740f751", "nome": "Leite", "quantidade": 2.0, "unidade": "litro", "valor_unitario": "5.50", "validade": "2026-08-01", "atualizado_em": "2026-07-24T21:00:38.898690"},
  {"id": "ebba31e2-3a8d-403f-95af-c19631bb57cf", "usuario_id": "6259aa48-da8b-40aa-be9d-31d6b8e4fb1a", "nome": "Cafe", "quantidade": 11.0, "unidade": "pacote", "valor_unitario": "3.00", "validade": null, "atualizado_em": "2026-07-25T17:47:58.264549"}
]
```

**PUT /itens/{id}**

```bash
curl -b cookies.txt -X PUT http://localhost:8000/itens/023aaf93-ff91-4471-8ce9-66298ecfa495 \
  -H "Content-Type: application/json" \
  -d '{"nome": "Leite Integral", "quantidade": 3, "unidade": "litro", "valor_unitario": 5.90, "validade": "2026-08-10"}'
```
```json
// 200 OK
{"id": "023aaf93-ff91-4471-8ce9-66298ecfa495", "usuario_id": "c8a21794-030b-4f9c-978b-65838740f751", "nome": "Leite Integral", "quantidade": 3.0, "unidade": "litro", "valor_unitario": "5.90", "validade": "2026-08-10", "atualizado_em": "2026-07-24T21:05:12.001234"}
```
Erro: `404 Not Found` (`{"detail": "Item nao encontrado"}`) se o id não existir.

**DELETE /itens/{id}**

```bash
curl -b cookies.txt -X DELETE http://localhost:8000/itens/023aaf93-ff91-4471-8ce9-66298ecfa495
```
`204 No Content` (sem corpo) em caso de sucesso.
Erros: `404 Not Found` se o id não existir; `409 Conflict` (`{"detail": "Nao e possivel excluir um item com movimentacoes registradas"}`) se o item já tiver movimentações — o histórico de gastos não pode ser apagado excluindo o item que ele referencia (ver seção 6).

### Movimentações e relatório de gastos

**POST /movimentacoes**

Registra uma entrada (reposição) ou saída (consumo), sempre vinculada ao usuário autenticado. `entrada` soma `quantidade` ao estoque; `saida` subtrai (bloqueada se não houver estoque suficiente). `valor_total` é sempre `quantidade × valor_unitario` do item **no momento da movimentação**, calculado no backend — o cliente nunca envia um valor, só a quantidade.

```bash
curl -b cookies.txt -X POST http://localhost:8000/movimentacoes \
  -H "Content-Type: application/json" \
  -d '{"item_id": "ebba31e2-3a8d-403f-95af-c19631bb57cf", "tipo": "saida", "quantidade": 4}'
```
```json
// 201 Created
{"id": "7647422c-e0c8-448d-a0c9-a35bda21d315", "item_id": "ebba31e2-3a8d-403f-95af-c19631bb57cf", "usuario_id": "6259aa48-da8b-40aa-be9d-31d6b8e4fb1a", "tipo": "saida", "quantidade": 4.0, "valor_total": "12.00", "criado_em": "2026-07-25T17:47:58.266747"}
```
Erros: `404 Not Found` se `item_id` não existir. `400 Bad Request` (`{"detail": "Estoque insuficiente para essa saida"}`) se a saída pedida for maior que o estoque atual.

**GET /relatorios/gastos**

Soma o `valor_total` de todas as saídas do usuário autenticado num período, e devolve também a lista de movimentações usadas no cálculo. `data_inicio`/`data_fim` (`YYYY-MM-DD`) são opcionais — se omitidos, o período padrão é o mês corrente.

```bash
curl -b cookies.txt "http://localhost:8000/relatorios/gastos?data_inicio=2026-07-01&data_fim=2026-07-31"
```
```json
// 200 OK
{
  "usuario_id": "6259aa48-da8b-40aa-be9d-31d6b8e4fb1a",
  "data_inicio": "2026-07-01",
  "data_fim": "2026-07-31",
  "total_gasto": "12.00",
  "movimentacoes": [
    {"id": "7647422c-e0c8-448d-a0c9-a35bda21d315", "item_id": "ebba31e2-3a8d-403f-95af-c19631bb57cf", "usuario_id": "6259aa48-da8b-40aa-be9d-31d6b8e4fb1a", "tipo": "saida", "quantidade": 4.0, "valor_total": "12.00", "criado_em": "2026-07-25T17:47:58.266747"}
  ]
}
```

---

## 6. Decisões técnicas relevantes

### Por que UUID como chave primária (em vez de ID incremental)

Todas as chaves primárias (`usuarios`, `itens_estoque`, `movimentacoes`, `sessoes`) são UUID v4 gerados no próprio backend (`uuid.uuid4()`), nunca IDs sequenciais (`1, 2, 3...`). Um ID incremental permite que qualquer usuário autenticado tente adivinhar registros de outras pessoas só variando o número na URL (`/itens/1`, `/itens/2`...) — uma falha conhecida como IDOR (Insecure Direct Object Reference) / enumeração de recursos. Um UUID v4 é aleatório: não existe um "próximo" valor previsível para tentar.

### Como funciona a sessão via cookie HttpOnly

Login não devolve um token (JWT ou similar) no corpo da resposta para o frontend guardar. Em vez disso:

1. `POST /auth/login` valida e-mail/senha e cria uma linha na tabela `sessoes` (`id`, `usuario_id`, `expira_em` = agora + 7 dias).
2. O `id` dessa sessão é assinado com `itsdangerous` (usando `SECRET_KEY`) e devolvido num cookie `session_id` com `HttpOnly=True`, `SameSite=Lax` e `Secure` (ligado fora de `ENVIRONMENT=local`).
3. Em toda requisição a uma rota protegida, o navegador manda o cookie automaticamente (por isso o frontend usa `withCredentials: true` e o CORS precisa de `allow_credentials=True` com uma origem explícita — nunca `*`). O backend lê o cookie, confere a assinatura e verifica no banco se a sessão existe e não expirou.
4. `POST /auth/logout` apaga a linha da sessão no banco e remove o cookie — a sessão morre no servidor, não só no navegador.

**Por que `HttpOnly` e nunca `localStorage`:** um cookie `HttpOnly` não pode ser lido por JavaScript (`document.cookie` não o enxerga). Se o token ficasse em `localStorage`, um XSS conseguiria roubá-lo; com `HttpOnly`, mesmo que um XSS aconteça, o cookie de sessão continua inacessível ao script malicioso.

**Por que sessão no banco em vez de só um token assinado:** o cookie guarda apenas o *id* da sessão, nunca dados do usuário. Isso permite revogar uma sessão a qualquer momento (logout) apagando a linha no banco — um JWT autocontido continuaria "válido" até expirar, mesmo que se quisesse invalidá-lo antes.

A senha nunca é armazenada em texto puro, só o hash bcrypt (`senha_hash`, via `passlib`) — bcrypt é deliberadamente lento e usa salt, o que inviabiliza tanto descobrir a senha original quanto usar rainbow tables mesmo que o banco vaze.

### Escolhas de stack

- **Backend — FastAPI + SQLAlchemy + SQLite:** FastAPI valida e documenta a API automaticamente a partir dos schemas Pydantic (Swagger em `/docs` sem esforço extra), é assíncrono por padrão e tem tipagem nativa via type hints do Python. SQLAlchemy (ORM) mantém a modelagem do banco em código Python versionável, e SQLite é suficiente para o escopo do desafio (arquivo único, zero configuração) — a troca para Postgres é só mudar `DATABASE_URL`, já que o SQLAlchemy abstrai o driver.
- **Frontend — React + TypeScript (Vite):** TypeScript pega erros de contrato com a API em tempo de compilação (ex.: um campo renomeado no backend quebra o build do frontend, não só em produção). Vite dá build/HMR rápido sem configuração manual de bundler. React + `react-router-dom` é o ecossistema mais direto para uma SPA pequena com rotas protegidas.

**Arquitetura em camadas (backend):** `routers` só valida a requisição (via `schema`) e repassa para um `service`; `services` concentram a regra de negócio isolada de HTTP (testável sem servidor rodando); `models` descreve como o dado é persistido, propositalmente separado de `schemas` (como o dado trafega pela API) — uma mudança interna no banco não vira automaticamente uma mudança pública na API. O frontend replica o mesmo princípio: `pages` decide o que aparece na tela, `hooks` decide de onde vêm os dados (nenhuma página chama `axios` diretamente).

**Modelagem de dados:** `movimentacoes` guarda tanto `item_id` quanto `usuario_id` — sem o `usuario_id` na própria movimentação, seria impossível calcular "quanto cada pessoa gastou" numa geladeira compartilhada, já que quem consome não é necessariamente quem cadastrou o item.

---

## 7. Decisões e trade-offs conscientes

Dado o prazo do desafio, alguns pontos foram deliberadamente deixados de fora do escopo — não por desconhecimento, mas por priorização. Registro do trade-off e de como cada um seria resolvido em produção:

| Trade-off | Por que ficou de fora agora | Como resolver em produção |
|---|---|---|
| **Sem rate limiting em `/auth/login`** | Não há limite de tentativas de senha por IP/usuário — um atacante pode tentar força bruta indefinidamente. Implementar isso bem (armazenamento de contadores, janelas de tempo, resposta consistente) é um escopo à parte do desafio em si. | Middleware de rate limiting (ex.: `slowapi`/`fastapi-limiter` com Redis) por IP e por e-mail, ou bloqueio temporário de conta após N tentativas falhas seguidas. Em produção, isso também costuma ficar no API gateway/WAF, não só na aplicação. |
| **Sem limpeza automática de sessões expiradas** | `get_current_user` já trata sessão expirada como não-autenticado (`expira_em < agora`), então não é um bug funcional — mas a linha nunca é removida da tabela `sessoes`, que cresce indefinidamente. | Um job periódico (cron, ou Celery beat) rodando `DELETE FROM sessoes WHERE expira_em < now()`, ou aproveitar o próprio `POST /auth/login` para apagar sessões expiradas do mesmo usuário antes de criar uma nova. |
| **Sem lock explícito na checagem de estoque antes de gravar a saída** | `registrar_movimentacao` lê `item.quantidade`, decide se há estoque suficiente, e só depois grava — sem lock entre a leitura e a escrita. Em teoria, duas saídas simultâneas do mesmo item poderiam ambas "ver" estoque suficiente e deixar a quantidade negativa. Na prática, o SQLite usado aqui serializa escritas dentro de um único processo, então o risco real é baixíssimo neste escopo. | Em Postgres com múltiplos workers, a proteção correta seria `SELECT ... FOR UPDATE` na linha do item dentro da transação (lock pessimista), ou uma constraint `CHECK (quantidade >= 0)` no banco como rede de segurança independente da aplicação. |
| **Imagens Docker sem volume de código / hot-reload** | `docker-compose.yml` não monta o código como volume — as imagens copiam o código no build (`COPY . .`), então mudar um arquivo local não reflete no container rodando. Simples e previsível (a imagem é sempre exatamente o que foi commitado), mas exige `docker compose up --build` a cada mudança. | Montar `./backend:/app` e `./frontend:/app` como bind mount (com um volume nomeado separado para `node_modules`, para não sobrescrever o que foi instalado no build) e manter `--reload`/Vite HMR ativos — é o padrão para ambiente de desenvolvimento em Docker. |

---

## 8. Como rodar com Docker Compose

Alternativa a rodar backend e frontend manualmente (seções 2 e 3): sobe os dois serviços com um único comando, cada um na sua própria imagem.

```powershell
copy backend\.env.example backend\.env    # se ainda nao existir — o compose le esse arquivo
docker compose up --build
```

- Backend em `http://localhost:8000` (`/docs` para o Swagger).
- Frontend em `http://localhost:5173`.
- `Ctrl+C` para parar; `docker compose down` remove os containers (os dados do banco continuam no volume nomeado `backend_data`); `docker compose down -v` remove o volume também, apagando os dados.

Rodar de novo depois de mudar código exige `--build` (as imagens são construídas uma vez, com o código copiado para dentro — não há volume de código montado, então elas não atualizam sozinhas; ver seção 7).

**O que cada `Dockerfile` faz:**

- **`backend/Dockerfile`**: parte de `python:3.13-slim`, instala as dependências do `requirements.txt`, copia o código, e sobe `uvicorn main:app --host 0.0.0.0 --port 8000`. O `--host 0.0.0.0` é obrigatório — sem ele o uvicorn só aceita conexões de dentro do próprio container, mesmo com a porta publicada no `docker-compose.yml`.
- **`frontend/Dockerfile`**: parte de `node:22-slim`, instala as dependências via `npm ci` (instala exatamente o que está no `package-lock.json`, mais rápido e previsível que `npm install` para builds), copia o código, e sobe `npm run dev -- --host 0.0.0.0` — mesmo motivo do `--host` do backend: o Vite por padrão só escuta em `localhost` dentro do container.

**Como os dois serviços se comunicam:** na verdade, o backend e o frontend **não conversam entre si dentro da rede do Docker**. Quem fala com o backend é o **navegador**, rodando na máquina host — e o frontend é só uma SPA (React) que o navegador baixa e executa localmente. Por isso `src/api/client.ts` continua apontando para `http://localhost:8000` mesmo em Docker: graças ao mapeamento de portas (`ports: "8000:8000"` no `docker-compose.yml`), o container do backend fica acessível em `localhost:8000` a partir do host — que é exatamente onde o navegador está. Se o frontend tentasse chamar `http://backend:8000` (o nome do serviço, que só existe na rede interna do Docker), o navegador não conseguiria resolver esse endereço, porque `backend` só é um hostname válido *para outros containers*, não para a máquina host.

**Persistência do banco:** o `docker-compose.yml` sobrescreve `DATABASE_URL` para `sqlite:///./data/geladeira.db` e monta um volume nomeado (`backend_data`) em `/app/data` dentro do container do backend. Isso separa o ciclo de vida dos dados do ciclo de vida do container: `docker compose down` (sem `-v`) remove os containers, mas o volume continua existindo, então o próximo `docker compose up` volta com os mesmos dados — testado no desenvolvimento deste projeto (cadastrei um usuário, derrubei e subi os containers de novo, o login continuou funcionando).

---

## Resumo para revisão rápida (roteiro de entrevista)

- **Autenticação:** sessão via cookie `HttpOnly` + `SameSite=Lax` + `Secure` (fora de local), id da sessão assinado com `itsdangerous`, sessão validada no banco (revogável no logout) — nunca JWT autocontido, nunca token em `localStorage`.
- **Senha:** hash bcrypt via `passlib`, nunca texto puro; `max_length=72` no schema porque o próprio bcrypt trunca/rejeita além disso.
- **UUID em vez de ID incremental:** evita IDOR/enumeração de recursos (`/itens/1`, `/itens/2`...) em todas as tabelas com dado sensível ou vinculado a usuário.
- **Arquitetura em camadas:** `routers` (protocolo) → `services` (regra de negócio) → `models`/`schemas` (persistência vs. contrato de API) no backend; `pages` (UI) → `hooks` (dados) no frontend — cada camada muda por um motivo diferente.
- **Modelagem:** `movimentacoes` é o histórico de auditoria (entrada/saída, `usuario_id`, `valor_total` calculado no backend); por isso a exclusão de um item com movimentações é bloqueada (`409`) em vez de fazer cascade — apagar o item não pode apagar o histórico de gastos de quem consumiu.
- **Stack:** FastAPI + SQLAlchemy + SQLite no backend (tipado, autodocumentado, troca de banco é só mudar `DATABASE_URL`); Vite + React + TypeScript + Tailwind no frontend (tipagem end-to-end, build rápido).
- **Testes automatizados:** `pytest` + `TestClient` do FastAPI em `backend/tests/`, rodando contra um SQLite isolado (nunca o banco de desenvolvimento) — cobrem autenticação, proteção de rota, movimentação de estoque/gastos e o bloqueio de exclusão de item com histórico (regressão do bug do cascade delete).
- **Docker:** `docker-compose.yml` sobe backend e frontend em containers separados; eles não se comunicam pela rede interna do Docker — é o navegador, no host, que fala com os dois via `localhost` graças ao mapeamento de portas. O banco SQLite persiste num volume nomeado entre `down`/`up`.
- **Trade-offs conscientes e por quê:** sem rate limiting no login, sem limpeza de sessões expiradas, sem lock explícito na checagem de estoque, sem hot-reload nas imagens Docker — todos de baixo risco real no escopo atual, todos com uma solução conhecida e citável para produção (seção 7).
