import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Lote, LoteAtualizarPayload } from '../types/lote'
import type { EntradaPayload, SaidaPayload } from '../types/movimentacao'

export function useLotes() {
  // A API devolve só lotes com quantidade > 0, já ordenados por vencimento.
  const [lotes, setLotes] = useState<Lote[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  const carregarLotes = useCallback(async () => {
    setErro(null)
    try {
      const resposta = await api.get<Lote[]>('/lotes')
      setLotes(resposta.data)
    } catch {
      setErro('Não foi possível carregar os lotes')
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregarLotes()
  }, [carregarLotes])

  // Entrada e saída não mexem no lote direto: são movimentações (ficam no
  // histórico). Depois de cada uma, recarrega a lista em vez de calcular
  // localmente — a entrada pode somar num lote existente ou criar outro, e a
  // saída pode zerar o lote (que então some da lista).

  async function registrarEntrada(dados: EntradaPayload) {
    await api.post('/movimentacoes/entrada', dados)
    await carregarLotes()
  }

  async function registrarSaida(dados: SaidaPayload) {
    await api.post('/movimentacoes/saida', dados)
    await carregarLotes()
  }

  // Recarrega em vez de trocar só o item: mudar a data do teste muda o
  // vencimento, e com ele a ordem da lista.
  async function atualizarLote(id: string, dados: LoteAtualizarPayload) {
    await api.put(`/lotes/${id}`, dados)
    await carregarLotes()
  }

  return {
    lotes,
    carregando,
    erro,
    registrarEntrada,
    registrarSaida,
    atualizarLote,
    recarregar: carregarLotes,
  }
}
