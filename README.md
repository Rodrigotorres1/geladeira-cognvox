# Sistema de Controle de Estoque de Geladeira

Aplicação full stack para controle de estoque, consumo e gastos de uma geladeira compartilhada entre colaboradores.

## Estrutura do projeto

```
/backend   # API em FastAPI + SQLAlchemy
/frontend  # Aplicação React + TypeScript
```

## Backend

### Como rodar

```powershell
cd backend
python -m venv venv                   # se o venv ainda não existir
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Copie `backend/.env.example` para `backend/.env` e ajuste os valores antes de rodar (veja a seção de variáveis de ambiente abaixo).

Com o servidor rodando:
- `http://localhost:8000/health` retorna `{"status": "ok"}`
- `http://localhost:8000/docs` abre a documentação interativa (Swagger) gerada automaticamente pelo FastAPI

### Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | String de conexão do banco (ex.: `sqlite:///./geladeira.db`) |
| `SECRET_KEY` | Chave usada para assinar a sessão do usuário; deve ser um valor aleatório e secreto em produção |
| `FRONTEND_ORIGIN` | Origem permitida no CORS (ex.: `http://localhost:5173`), precisa bater exatamente com a URL do frontend para os cookies de sessão funcionarem |
| `ENVIRONMENT` | `local` para desenvolvimento (cookie de sessão sem `Secure`, funciona em `http://localhost`); qualquer outro valor (ex.: `production`) ativa `Secure=True` no cookie |

### Arquitetura em camadas

O código do backend fica organizado dentro de `backend/app/` em cinco pastas, cada uma com uma única responsabilidade:

```
app/
├── core/      # configuração e infraestrutura (env vars, conexão com o banco)
├── models/    # tabelas do banco (SQLAlchemy)
├── schemas/   # formato de entrada/saída da API (Pydantic)
├── routers/   # rotas HTTP: recebem a requisição e chamam um service
└── services/  # regras de negócio
```

**Por que separar assim?** Numa API pequena seria tentador colocar tudo dentro da própria rota: receber a requisição, validar, consultar o banco e devolver a resposta, tudo na mesma função. O problema é que isso mistura três coisas que mudam por motivos diferentes:

- **A rota** muda quando muda o *protocolo* (ex.: virar `PATCH` em vez de `PUT`, mudar um path).
- **A regra de negócio** muda quando muda a *lógica do domínio* (ex.: "consumo não pode deixar o estoque negativo").
- **O modelo de dados** muda quando muda o *schema do banco* (ex.: adicionar uma coluna).

Se as três coisas estão misturadas na mesma função, qualquer mudança em uma delas arrisca quebrar as outras duas sem querer, e fica difícil testar a regra de negócio sem precisar simular uma requisição HTTP inteira. Separando em camadas:

- `models` descreve como o dado é **persistido**; `schemas` descreve como o dado **trafega pela API**. São propositalmente diferentes — se fossem a mesma coisa, qualquer mudança interna no banco (ex.: renomear uma coluna) viraria automaticamente uma mudança pública na API, quebrando o frontend sem necessidade.
- `routers` só faz o trabalho de "porteiro": recebe a requisição, valida o formato via `schema` e repassa para um `service`. Não decide nada sobre regra de negócio.
- `services` concentra a lógica de negócio isolada de HTTP, então dá para testá-la diretamente (passando dados e checando o resultado) sem precisar de um servidor rodando.
- `core` fica de fora de tudo isso porque não é sobre negócio nem sobre API — é configuração e infraestrutura que todas as outras camadas podem usar.

Na prática, isso segue o princípio de responsabilidade única: cada camada tem um único motivo para mudar, o que torna o código mais fácil de testar, revisar e evoluir sem efeitos colaterais inesperados.

### Modelagem de dados

O schema (em `backend/app/models/`) tem três tabelas:

```
usuarios  1───N  itens_estoque  1───N  movimentacoes
   │                                        │
   └────────────────────────────────────────┘
              (usuario_id também em movimentacoes,
               registra quem fez a movimentação)
```

- **`usuarios`**: nome, e-mail (único), hash da senha, data de criação.
- **`itens_estoque`**: pertence a um usuário (quem cadastrou o item), com nome, quantidade, unidade, valor unitário e validade opcional.
- **`movimentacoes`**: entrada (compra/reposição) ou saída (consumo) de um item, sempre vinculada ao usuário que realizou a ação e com o valor total gasto naquela movimentação — é essa tabela que alimenta o relatório de gastos por usuário/período.
- **`sessoes`**: sessão de login do usuário (id da sessão, `usuario_id`, `criado_em`, `expira_em`) — ver seção de autenticação abaixo.

**Por que UUID em vez de ID incremental:** todas as chaves primárias são UUID v4 gerados no próprio backend (`uuid.uuid4()`), nunca IDs sequenciais do tipo `1, 2, 3...`. Um ID incremental permite que qualquer usuário autenticado tente adivinhar registros de outras pessoas só variando o número na URL (ex.: `GET /itens/1`, `/itens/2`, `/itens/3`) — esse tipo de falha é conhecido como IDOR (Insecure Direct Object Reference)/enumeração de recursos. Um UUID v4 é gerado a partir de dados aleatórios, então não há um "próximo" valor previsível para tentar.

**Por que os relacionamentos fazem sentido para o problema:** o domínio é literalmente uma cadeia de posse — um usuário cadastra itens, e cada item acumula um histórico de movimentações que também precisa saber *quem* a realizou (não necessariamente quem cadastrou o item, já que a geladeira é compartilhada). Por isso `movimentacoes` guarda tanto `item_id` quanto `usuario_id`: sem o `usuario_id` na própria movimentação, seria impossível calcular "quanto cada pessoa gastou", que é um requisito central do desafio.

### Autenticação e sessão

Login não usa token (JWT ou similar) devolvido no corpo da resposta para o frontend guardar. Em vez disso:

1. `POST /auth/login` valida e-mail/senha e cria uma linha na tabela `sessoes` (id da sessão, `usuario_id`, `expira_em` = agora + 7 dias).
2. O id dessa sessão é assinado com `itsdangerous` (usando `SECRET_KEY`) e devolvido em um cookie `session_id` com `HttpOnly=True`, `SameSite=Lax` e `Secure` (ligado fora de ambiente local).
3. Em toda requisição a uma rota protegida, o navegador manda esse cookie automaticamente (por isso o frontend precisa usar `credentials: "include"`/`withCredentials: true` e o CORS precisa de `allow_credentials=True` com uma origem explícita). O backend lê o cookie, verifica a assinatura e confere no banco se a sessão existe e não expirou.
4. `POST /auth/logout` apaga a linha da sessão no banco e remove o cookie — a sessão morre no servidor, não só no navegador.

**Por que HttpOnly e nunca `localStorage`:** um cookie `HttpOnly` não pode ser lido por JavaScript (`document.cookie` não o enxerga). Se o token de sessão fosse guardado em `localStorage`, qualquer script malicioso injetado na página via XSS conseguiria roubá-lo e agir como o usuário. Com `HttpOnly`, mesmo que um XSS aconteça, o atacante não consegue ler o cookie de sessão.

**Por que sessão no banco em vez de só um token assinado:** o cookie guarda apenas o *id* da sessão, nunca dados do usuário. Isso permite revogar uma sessão a qualquer momento (logout, ou um admin encerrando sessões) simplesmente apagando a linha no banco — um JWT autocontido, por comparação, continua "válido" até expirar mesmo que você quisesse invalidá-lo antes.

**Por que a senha é armazenada em hash:** a senha em si nunca é salva, só o resultado de um hash bcrypt (`senha_hash`). Bcrypt é deliberadamente lento e usa "salt", o que torna inviável tanto descobrir a senha original a partir do hash quanto usar tabelas pré-computadas (rainbow tables) para quebrá-la. Mesmo que o banco vaze, as senhas continuam protegidas.

### Rotas da API implementadas

| Método | Rota | Descrição | Autenticação |
|---|---|---|---|
| POST | `/auth/registro` | Cria um novo usuário | Não |
| POST | `/auth/login` | Autentica e define o cookie de sessão | Não |
| POST | `/auth/logout` | Invalida a sessão e remove o cookie | Sim (cookie) |
| GET | `/auth/me` | Retorna os dados do usuário autenticado | Sim (cookie) |

> **Nota sobre `curl` no Windows:** dentro do PowerShell, `curl` é apenas um apelido para `Invoke-WebRequest`, que **não** aceita as flags `-c`/`-b`/`-d` do curl real (dá erro de parâmetro ambíguo). Os exemplos abaixo trazem as duas versões: `curl` (Git Bash/WSL/Linux/macOS, ou `curl.exe` explicitamente no Windows) e PowerShell nativo com `Invoke-RestMethod -SessionVariable`.

**POST /auth/registro**

```bash
curl -X POST http://localhost:8000/auth/registro \
  -H "Content-Type: application/json" \
  -d '{"nome": "Rodrigo", "email": "rodrigo@teste.com", "senha": "senha1234"}'
```
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/auth/registro" -Method Post `
  -ContentType "application/json" `
  -Body '{"nome": "Rodrigo", "email": "rodrigo@teste.com", "senha": "senha1234"}'
```
```json
// 201 Created
{"id": "5eabe54b-3a06-4089-8e95-584185758bd4", "nome": "Rodrigo", "email": "rodrigo@teste.com", "criado_em": "2026-07-24T17:34:04.749696"}
```
`409 Conflict` se o e-mail já existe. `422 Unprocessable Entity` se a senha tiver menos de 8 caracteres ou o e-mail for inválido.

**POST /auth/login**

```bash
curl -c cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "rodrigo@teste.com", "senha": "senha1234"}'
```
`-c cookies.txt` salva o cookie `session_id` recebido.

```powershell
$resp = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method Post `
  -ContentType "application/json" `
  -Body '{"email": "rodrigo@teste.com", "senha": "senha1234"}' `
  -SessionVariable session
```
`-SessionVariable session` guarda o cookie na variável `$session`, que é reaproveitada nas chamadas seguintes. `401 Unauthorized` se e-mail/senha não conferirem.

**GET /auth/me**

```bash
curl -b cookies.txt http://localhost:8000/auth/me
```
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/auth/me" -WebSession $session
```
`401 Unauthorized` sem cookie válido.

**POST /auth/logout**

```bash
curl -b cookies.txt -c cookies.txt -X POST http://localhost:8000/auth/logout
```
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/auth/logout" -Method Post -WebSession $session
```
`204 No Content`. Depois disso, `/auth/me` volta a responder `401`.

No Swagger (`/docs`) o fluxo é o mesmo: chame `/auth/login` pelo botão "Try it out", e o navegador guarda o cookie automaticamente para as chamadas seguintes na mesma aba — não precisa copiar nada manualmente.

### Rotas de itens do estoque

Todas exigem sessão válida (cookie `session_id`) — sem ela, qualquer uma retorna `401 Unauthorized`. A geladeira é compartilhada, então `GET /itens` lista os itens de todos os usuários; `POST /itens` vincula o item criado ao usuário autenticado (`usuario_id`), mas qualquer usuário logado pode editar (`PUT`) ou remover (`DELETE`) qualquer item.

| Método | Rota | Descrição |
|---|---|---|
| GET | `/itens` | Lista todos os itens do estoque |
| POST | `/itens` | Cria um item, vinculado ao usuário autenticado |
| PUT | `/itens/{id}` | Atualiza um item existente (substituição completa dos campos) |
| DELETE | `/itens/{id}` | Remove um item |

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
`validade` é opcional (pode omitir). `422 Unprocessable Entity` se `quantidade` ou `valor_unitario` forem negativos.

**GET /itens**

```bash
curl -b cookies.txt http://localhost:8000/itens
```

**PUT /itens/{id}**

```bash
curl -b cookies.txt -X PUT http://localhost:8000/itens/023aaf93-ff91-4471-8ce9-66298ecfa495 \
  -H "Content-Type: application/json" \
  -d '{"nome": "Leite Integral", "quantidade": 3, "unidade": "litro", "valor_unitario": 5.90, "validade": "2026-08-10"}'
```
`404 Not Found` com `{"detail": "Item nao encontrado"}` se o id não existir.

**DELETE /itens/{id}**

```bash
curl -b cookies.txt -X DELETE http://localhost:8000/itens/023aaf93-ff91-4471-8ce9-66298ecfa495
```
`204 No Content` em caso de sucesso; `404 Not Found` se o id não existir.

Em PowerShell, troque `curl -b cookies.txt` por `Invoke-RestMethod -WebSession $session` (mesma lógica dos exemplos de autenticação acima), e `-X POST`/`-X PUT`/`-X DELETE` por `-Method Post`/`-Method Put`/`-Method Delete`.
