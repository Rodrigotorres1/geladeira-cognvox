import axios from 'axios'

// Fallback para localhost:8000 garante que "npm run dev" continue funcionando
// sem precisar de nenhum .env local — só é preciso configurar VITE_API_URL de
// verdade no ambiente de deploy (ex.: Vercel), apontando pro backend real.
const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL,
  withCredentials: true,
})
