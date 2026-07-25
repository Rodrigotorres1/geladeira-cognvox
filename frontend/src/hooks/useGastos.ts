import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { MovimentacaoCriarPayload, RelatorioGastos } from '../types/movimentacao'

// dataInicio/dataFim vazias -> nao manda o parametro -> backend usa o mes
// atual como padrao (mesma regra de GET /relatorios/gastos).
export function useGastos(dataInicio: string, dataFim: string) {
  const [relatorio, setRelatorio] = useState<RelatorioGastos | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  const carregarRelatorio = useCallback(async () => {
    setCarregando(true)
    setErro(null)
    try {
      const resposta = await api.get<RelatorioGastos>('/relatorios/gastos', {
        params: {
          data_inicio: dataInicio || undefined,
          data_fim: dataFim || undefined,
        },
      })
      setRelatorio(resposta.data)
    } catch {
      setErro('Não foi possível carregar o relatório de gastos')
    } finally {
      setCarregando(false)
    }
  }, [dataInicio, dataFim])

  useEffect(() => {
    carregarRelatorio()
  }, [carregarRelatorio])

  // Propaga o erro (sem catch aqui) pelo mesmo motivo do useItens: quem
  // chama e o formulario, que sabe mostrar uma mensagem especifica
  // (ex.: "estoque insuficiente") em vez de um erro generico.
  async function registrarSaida(dados: MovimentacaoCriarPayload) {
    await api.post('/movimentacoes', dados)
    await carregarRelatorio()
  }

  return { relatorio, carregando, erro, registrarSaida, recarregar: carregarRelatorio }
}
