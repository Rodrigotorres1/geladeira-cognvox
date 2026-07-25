import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { useGastos } from '../hooks/useGastos'
import { useItens } from '../hooks/useItens'
import { extrairMensagemErro } from '../lib/erros'
import type { MovimentacaoOut } from '../types/movimentacao'

interface PontoGrafico {
  data: string
  total: number
}

// Agrupa as movimentacoes (que a API devolve uma a uma) por dia, somando
// o valor_total de cada uma — e isso que vira cada barra do grafico.
function agruparGastosPorDia(movimentacoes: MovimentacaoOut[]): PontoGrafico[] {
  const totaisPorDia = new Map<string, number>()
  for (const mov of movimentacoes) {
    const dia = mov.criado_em.slice(0, 10)
    totaisPorDia.set(dia, (totaisPorDia.get(dia) ?? 0) + Number(mov.valor_total))
  }
  return Array.from(totaisPorDia.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([dia, total]) => ({
      data: formatarDataCurta(dia),
      total: Number(total.toFixed(2)),
    }))
}

function formatarDataCurta(data: string) {
  const [, mes, dia] = data.split('-')
  return `${dia}/${mes}`
}

function formatarDataBR(data: string) {
  const [ano, mes, dia] = data.split('-')
  return `${dia}/${mes}/${ano}`
}

function formatarMoeda(valor: string | number) {
  return `R$ ${Number(valor).toFixed(2)}`
}

export function Gastos() {
  const [dataInicio, setDataInicio] = useState('')
  const [dataFim, setDataFim] = useState('')
  const { relatorio, carregando, erro, registrarSaida } = useGastos(dataInicio, dataFim)
  const { itens, recarregar: recarregarItens } = useItens()

  const [itemId, setItemId] = useState('')
  const [quantidade, setQuantidade] = useState('')
  const [erroRegistro, setErroRegistro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function handleSubmit(evento: FormEvent) {
    evento.preventDefault()
    setErroRegistro(null)
    setEnviando(true)
    try {
      await registrarSaida({ item_id: itemId, tipo: 'saida', quantidade: Number(quantidade) })
      await recarregarItens()
      setItemId('')
      setQuantidade('')
    } catch (err) {
      setErroRegistro(extrairMensagemErro(err, 'Não foi possível registrar a saída.'))
    } finally {
      setEnviando(false)
    }
  }

  const dadosGrafico = relatorio ? agruparGastosPorDia(relatorio.movimentacoes) : []

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-gray-900">Gastos</h1>

      <Card>
        <h2 className="mb-4 text-sm font-medium text-gray-700">Período</h2>
        <div className="grid grid-cols-2 gap-4 sm:max-w-sm">
          <Input
            id="data-inicio"
            label="Data início"
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
          />
          <Input
            id="data-fim"
            label="Data fim"
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
          />
        </div>
      </Card>

      {erro && <p className="text-sm font-medium text-red-600">{erro}</p>}

      {carregando ? (
        <p className="text-gray-500">Carregando relatório...</p>
      ) : (
        relatorio && (
          <>
            <Card>
              <p className="text-sm text-gray-600">
                Total gasto de {formatarDataBR(relatorio.data_inicio)} a{' '}
                {formatarDataBR(relatorio.data_fim)}
              </p>
              <p className="mt-1 text-3xl font-semibold text-gray-900">
                {formatarMoeda(relatorio.total_gasto)}
              </p>
            </Card>

            <Card>
              <h2 className="mb-4 text-sm font-medium text-gray-700">Gastos no período</h2>
              {dadosGrafico.length === 0 ? (
                <p className="text-gray-500">Nenhum gasto registrado nesse período.</p>
              ) : (
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dadosGrafico}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="data" tick={{ fontSize: 12, fill: '#6b7280' }} />
                      <YAxis
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                        tickFormatter={(valor) => `R$${valor}`}
                      />
                      <Tooltip formatter={(valor) => formatarMoeda(Number(valor))} />
                      <Bar dataKey="total" fill="#2563eb" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>
          </>
        )
      )}

      <Card>
        <h2 className="mb-4 text-sm font-medium text-gray-700">Registrar saída</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 sm:max-w-sm">
          <div className="flex flex-col gap-1">
            <label htmlFor="item" className="text-sm font-medium text-gray-700">
              Item
            </label>
            <select
              id="item"
              value={itemId}
              onChange={(e) => setItemId(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
              required
            >
              <option value="" disabled>
                Selecione um item
              </option>
              {itens.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome} ({item.quantidade} {item.unidade} em estoque)
                </option>
              ))}
            </select>
          </div>
          <Input
            id="quantidade-saida"
            label="Quantidade"
            type="number"
            min="0"
            step="any"
            value={quantidade}
            onChange={(e) => setQuantidade(e.target.value)}
            required
          />
          {erroRegistro && <p className="text-sm font-medium text-red-600">{erroRegistro}</p>}
          <Button type="submit" disabled={enviando}>
            {enviando ? 'Registrando...' : 'Registrar saída'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
