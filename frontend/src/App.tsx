import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { RequireAuth } from './components/RequireAuth'
import { Estoque } from './pages/Estoque'
import { Historico } from './pages/Historico'
import { Login } from './pages/Login'
import { Tipos } from './pages/Tipos'

function Protegida({ children }: { children: ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>
}

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/estoque" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/estoque" element={<Protegida><Estoque /></Protegida>} />
        <Route path="/tipos" element={<Protegida><Tipos /></Protegida>} />
        <Route path="/historico" element={<Protegida><Historico /></Protegida>} />
        <Route path="*" element={<Navigate to="/estoque" replace />} />
      </Routes>
    </Layout>
  )
}

export default App
