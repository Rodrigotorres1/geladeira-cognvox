import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { ItemAtualizarPayload, ItemCriarPayload, ItemEstoque } from '../types/item'

function ordenarPorNome(itens: ItemEstoque[]) {
  return [...itens].sort((a, b) => a.nome.localeCompare(b.nome))
}

export function useItens() {
  const [itens, setItens] = useState<ItemEstoque[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  const carregarItens = useCallback(async () => {
    setCarregando(true)
    setErro(null)
    try {
      const resposta = await api.get<ItemEstoque[]>('/itens')
      setItens(resposta.data)
    } catch {
      setErro('Não foi possível carregar os itens do estoque')
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregarItens()
  }, [carregarItens])

  // criarItem/atualizarItem/removerItem propagam o erro (não fazem catch) de
  // propósito: quem chama é um formulário/ação específica, que sabe melhor
  // que mensagem mostrar para aquele contexto do que este hook genérico.

  async function criarItem(dados: ItemCriarPayload) {
    const resposta = await api.post<ItemEstoque>('/itens', dados)
    setItens((atual) => ordenarPorNome([...atual, resposta.data]))
  }

  async function atualizarItem(id: string, dados: ItemAtualizarPayload) {
    const resposta = await api.put<ItemEstoque>(`/itens/${id}`, dados)
    setItens((atual) => ordenarPorNome(atual.map((item) => (item.id === id ? resposta.data : item))))
  }

  async function removerItem(id: string) {
    await api.delete(`/itens/${id}`)
    setItens((atual) => atual.filter((item) => item.id !== id))
  }

  // Entrada de estoque nao e um PUT no item: e uma movimentacao (POST
  // /movimentacoes), que fica registrada no historico. Por isso recarrega a
  // lista em vez de so somar localmente — o valor atualizado vem do backend.
  async function registrarEntrada(itemId: string, quantidade: number) {
    await api.post('/movimentacoes', { item_id: itemId, tipo: 'entrada', quantidade })
    await carregarItens()
  }

  return {
    itens,
    carregando,
    erro,
    criarItem,
    atualizarItem,
    removerItem,
    registrarEntrada,
    recarregar: carregarItens,
  }
}
