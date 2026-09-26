import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { RequireAuth } from './components/RequireAuth'
import { Estoque } from './pages/Estoque'
import { Gastos } from './pages/Gastos'
import { Login } from './pages/Login'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/estoque" replace />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/estoque"
          element={
            <RequireAuth>
              <Estoque />
            </RequireAuth>
          }
        />
        <Route
          path="/gastos"
          element={
            <RequireAuth>
              <Gastos />
            </RequireAuth>
          }
        />
      </Routes>
    </Layout>
  )
}

export default App
