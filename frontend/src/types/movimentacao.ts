import type { LoteResumo } from './lote'

export type TipoMovimentacao = 'entrada' | 'saida'

export interface Movimentacao {
  id: string
  lote: LoteResumo
  usuario_id: string
  tipo: TipoMovimentacao
  quantidade: number
  observacao: string | null
  criado_em: string
}

export interface EntradaPayload {
  tipo_id: string
  // Texto: o backend interpreta "MM/AAAA", "M/AAAA" ou "AAAA".
  data_teste: string
  quantidade: number
  numero_lote: string | null
  observacao: string | null
}

export interface SaidaPayload {
  lote_id: string
  quantidade: number
  observacao: string | null
}
