import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { usuario, carregando } = useAuth()

  if (carregando) {
    return <p className="text-center text-gray-500">Carregando...</p>
  }

  if (!usuario) {
    return <Navigate to="/login" replace />
  }

  return children
}
