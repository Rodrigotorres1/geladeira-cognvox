import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../api/client'

export interface Usuario {
  id: string
  nome: string
  email: string
  criado_em: string
}

interface AuthContextValue {
  usuario: Usuario | null
  carregando: boolean
  login: (email: string, senha: string) => Promise<void>
  registro: (nome: string, email: string, senha: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  // Só sabemos se existe sessão ativa depois que /auth/me responder; até lá,
  // RequireAuth não pode decidir se redireciona para /login ou não.
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    api
      .get<Usuario>('/auth/me')
      .then((resposta) => setUsuario(resposta.data))
      .catch(() => setUsuario(null))
      .finally(() => setCarregando(false))
  }, [])

  async function login(email: string, senha: string) {
    const resposta = await api.post<Usuario>('/auth/login', { email, senha })
    setUsuario(resposta.data)
  }

  async function registro(nome: string, email: string, senha: string) {
    await api.post('/auth/registro', { nome, email, senha })
    // /auth/registro só cria o usuário, não abre sessão (não define cookie);
    // por isso logamos em seguida com as mesmas credenciais.
    await login(email, senha)
  }

  async function logout() {
    await api.post('/auth/logout')
    setUsuario(null)
  }

  return (
    <AuthContext.Provider value={{ usuario, carregando, login, registro, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth precisa ser usado dentro de um AuthProvider')
  }
  return context
}
