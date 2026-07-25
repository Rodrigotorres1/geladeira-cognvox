import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Button } from './ui/Button'

function classeLink({ isActive }: { isActive: boolean }) {
  return `text-sm font-medium transition-colors ${
    isActive ? 'text-primary' : 'text-gray-500 hover:text-gray-900'
  }`
}

export function Layout({ children }: { children: ReactNode }) {
  const { usuario, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-8">
            <span className="text-lg font-semibold text-gray-900">Geladeira Cognvox</span>
            {usuario && (
              <nav className="flex items-center gap-6">
                <NavLink to="/estoque" className={classeLink}>
                  Estoque
                </NavLink>
                <NavLink to="/gastos" className={classeLink}>
                  Gastos
                </NavLink>
              </nav>
            )}
          </div>
          {usuario && (
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{usuario.nome}</span>
              <Button variant="secondary" onClick={() => logout()}>
                Sair
              </Button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
    </div>
  )
}
