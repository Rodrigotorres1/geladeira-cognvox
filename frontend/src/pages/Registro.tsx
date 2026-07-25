import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'

export function Registro() {
  const { registro } = useAuth()
  const navigate = useNavigate()
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function handleSubmit(evento: FormEvent) {
    evento.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      await registro(nome, email, senha)
      navigate('/estoque')
    } catch {
      setErro('Não foi possível criar a conta (email já cadastrado ou senha muito curta)')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <Card className="w-full max-w-sm">
        <h1 className="mb-6 text-xl font-semibold text-gray-900">Criar conta</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            id="nome"
            label="Nome"
            type="text"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
          />
          <Input
            id="email"
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            id="senha"
            label="Senha (mínimo 8 caracteres)"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            minLength={8}
            required
          />
          {erro && <p className="text-sm font-medium text-red-600">{erro}</p>}
          <Button type="submit" disabled={enviando} className="mt-2 w-full">
            {enviando ? 'Cadastrando...' : 'Cadastrar'}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Já tem conta?{' '}
          <Link to="/login" className="text-primary font-medium hover:underline">
            Entrar
          </Link>
        </p>
      </Card>
    </div>
  )
}
