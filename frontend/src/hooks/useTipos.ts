import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { TipoCilindro, TipoPayload } from '../types/tipo'

function ordenarPorNome(tipos: TipoCilindro[]) {
  return [...tipos].sort((a, b) => a.nome.localeCompare(b.nome))
}

export function useTipos() {
  const [tipos, setTipos] = useState<TipoCilindro[]>([])
  // Só a primeira carga mostra "Carregando...": recarregar depois de uma
  // movimentação atualiza a lista sem sumir com a tela.
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  const carregarTipos = useCallback(async () => {
    setErro(null)
    try {
      const resposta = await api.get<TipoCilindro[]>('/tipos')
      setTipos(resposta.data)
    } catch {
      setErro('Não foi possível carregar os tipos de cilindro')
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregarTipos()
  }, [carregarTipos])

  // As mutações propagam o erro (não fazem catch) de propósito: quem chama é
  // um formulário/ação, que sabe que mensagem mostrar naquele contexto.

  async function criarTipo(dados: TipoPayload) {
    const resposta = await api.post<TipoCilindro>('/tipos', dados)
    setTipos((atual) => ordenarPorNome([...atual, resposta.data]))
  }

  async function atualizarTipo(id: string, dados: TipoPayload) {
    const resposta = await api.put<TipoCilindro>(`/tipos/${id}`, dados)
    setTipos((atual) => ordenarPorNome(atual.map((tipo) => (tipo.id === id ? resposta.data : tipo))))
  }

  async function removerTipo(id: string) {
    await api.delete(`/tipos/${id}`)
    setTipos((atual) => atual.filter((tipo) => tipo.id !== id))
  }

  return {
    tipos,
    carregando,
    erro,
    criarTipo,
    atualizarTipo,
    removerTipo,
    recarregar: carregarTipos,
  }
}
