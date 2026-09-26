import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Button } from './ui/Button'

function classeLink({ isActive }: { isActive: boolean }) {
  return `py-1 text-sm font-medium transition-colors ${
    isActive ? 'text-primary' : 'text-gray-500 hover:text-gray-900'
  }`
}

export function Layout({ children }: { children: ReactNode }) {
  const { usuario, logout } = useAuth()

  return (
    <div className="min-h-dvh bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        {/* No celular: título + Sair na primeira linha e a navegação inteira
            na segunda; a partir de sm tudo numa linha só. */}
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-8 gap-y-2 px-4 py-3">
          <span className="text-lg font-semibold text-gray-900">Cilindros de O₂</span>
          {usuario && (
            <nav className="order-last flex w-full gap-6 sm:order-none sm:w-auto sm:flex-1">
              <NavLink to="/estoque" className={classeLink}>
                Estoque
              </NavLink>
              <NavLink to="/tipos" className={classeLink}>
                Tipos
              </NavLink>
              <NavLink to="/historico" className={classeLink}>
                Histórico
              </NavLink>
            </nav>
          )}
          {usuario && (
            <div className="flex items-center gap-4">
              <span className="hidden text-sm text-gray-600 sm:inline">{usuario.nome}</span>
              <Button variant="secondary" onClick={() => logout()}>
                Sair
              </Button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-5 sm:py-8">{children}</main>
    </div>
  )
}
