import tailwindcss from '@tailwindcss/vite'
import { defineConfig, loadEnv } from 'vite'
import type { ProxyOptions } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Sem o prefixo VITE_: é configuração do servidor do Vite, não vai para o
  // bundle do navegador. No docker-compose aponta para http://backend:8000
  // (dentro do container, "localhost" é o próprio frontend).
  const env = loadEnv(mode, process.cwd(), '')
  const alvoApi = env.API_PROXY_TARGET || 'http://localhost:8000'

  // Mesmo papel do rewrite /api/:path* do vercel.json: /api/tipos -> <alvo>/tipos.
  const proxy: Record<string, ProxyOptions> = {
    '/api': {
      target: alvoApi,
      changeOrigin: true,
      rewrite: (caminho) => caminho.replace(/^\/api/, ''),
    },
  }

  return {
    plugins: [react(), tailwindcss()],
    server: { proxy },
    // `vite preview` (build de produção servido localmente) com o mesmo proxy.
    preview: { proxy },
  }
})
