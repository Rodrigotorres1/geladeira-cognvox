import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Movimentacao } from '../types/movimentacao'

// Histórico (somente leitura): registrar entrada/saída fica no useLotes,
// junto da lista que essas ações alteram.
export function useMovimentacoes() {
  const [movimentacoes, setMovimentacoes] = useState<Movimentacao[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  const carregarMovimentacoes = useCallback(async () => {
    setErro(null)
    try {
      const resposta = await api.get<Movimentacao[]>('/movimentacoes')
      setMovimentacoes(resposta.data)
    } catch {
      setErro('Não foi possível carregar o histórico')
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregarMovimentacoes()
  }, [carregarMovimentacoes])

  return { movimentacoes, carregando, erro, recarregar: carregarMovimentacoes }
}
