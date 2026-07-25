FROM python:3.13-slim

WORKDIR /app

# Copia so o requirements.txt primeiro para o Docker cachear a camada de
# dependencias — ela so e reinstalada quando requirements.txt muda, nao a
# cada alteracao de codigo.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Diretorio onde o SQLite grava o arquivo do banco quando DATABASE_URL
# aponta para ./data/geladeira.db (ver docker-compose.yml) — precisa
# existir antes do volume nomeado ser montado em cima dele.
RUN mkdir -p data

EXPOSE 8000

# --host 0.0.0.0: por padrao o uvicorn escuta so em localhost, que dentro
# do container e o proprio container — inacessivel de fora mesmo com a
# porta publicada. 0.0.0.0 aceita conexoes de qualquer interface.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
