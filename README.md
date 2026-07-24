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

**Por que UUID em vez de ID incremental:** todas as chaves primárias são UUID v4 gerados no próprio backend (`uuid.uuid4()`), nunca IDs sequenciais do tipo `1, 2, 3...`. Um ID incremental permite que qualquer usuário autenticado tente adivinhar registros de outras pessoas só variando o número na URL (ex.: `GET /itens/1`, `/itens/2`, `/itens/3`) — esse tipo de falha é conhecido como IDOR (Insecure Direct Object Reference)/enumeração de recursos. Um UUID v4 é gerado a partir de dados aleatórios, então não há um "próximo" valor previsível para tentar.

**Por que os relacionamentos fazem sentido para o problema:** o domínio é literalmente uma cadeia de posse — um usuário cadastra itens, e cada item acumula um histórico de movimentações que também precisa saber *quem* a realizou (não necessariamente quem cadastrou o item, já que a geladeira é compartilhada). Por isso `movimentacoes` guarda tanto `item_id` quanto `usuario_id`: sem o `usuario_id` na própria movimentação, seria impossível calcular "quanto cada pessoa gastou", que é um requisito central do desafio.
