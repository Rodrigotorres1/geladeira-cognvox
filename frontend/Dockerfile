FROM node:22-slim

WORKDIR /app

# Copia so os manifestos primeiro para o Docker cachear a camada de
# dependencias — "npm ci" so roda de novo quando o lockfile muda.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# --host 0.0.0.0: o Vite, por padrao, escuta so em localhost dentro do
# container — inacessivel de fora mesmo com a porta publicada. Precisa
# aceitar conexoes de qualquer interface para o host conseguir acessar.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
