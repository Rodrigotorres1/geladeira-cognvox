export type TipoMovimentacao = 'entrada' | 'saida'

export interface MovimentacaoOut {
  id: string
  item_id: string
  usuario_id: string
  tipo: TipoMovimentacao
  quantidade: number
  valor_total: string
  criado_em: string
}

export interface RelatorioGastos {
  usuario_id: string
  data_inicio: string
  data_fim: string
  total_gasto: string
  movimentacoes: MovimentacaoOut[]
}

export interface MovimentacaoCriarPayload {
  item_id: string
  tipo: TipoMovimentacao
  quantidade: number
}
