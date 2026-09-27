import axios from 'axios'

// A API é sempre chamada pela mesma origem do frontend, em /api:
// - dev: o proxy do Vite (vite.config.ts) repassa /api para o backend local;
// - produção: o rewrite da Vercel (vercel.json) repassa /api para o Render.
// Para o navegador tudo é "mesmo site", então o cookie de sessão funciona com
// SameSite=Lax e não depende de CORS nem de cookie de terceiros.
export const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})
