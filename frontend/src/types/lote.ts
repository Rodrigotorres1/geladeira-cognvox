import type { TipoResumo } from './tipo'

export type StatusLote = 'ok' | 'atencao' | 'urgente' | 'vencido'

export interface Lote {
  id: string
  tipo: TipoResumo
  quantidade: number
  // data_teste vem como a usuária digitou ("04/2016" ou "2016");
  // vencimento sempre com mês ("01/2026").
  data_teste: string
  vencimento: string
  numero_lote: string | null
  criado_em: string
  meses_restantes: number
  status: StatusLote
}

export interface LoteResumo {
  id: string
  tipo: TipoResumo
  data_teste: string
  vencimento: string
  numero_lote: string | null
}

export interface LoteAtualizarPayload {
  data_teste: string
  numero_lote: string | null
}
