export interface ItemEstoque {
  id: string
  usuario_id: string
  nome: string
  quantidade: number
  unidade: string
  valor_unitario: string
  validade: string | null
  atualizado_em: string
}

export interface ItemCriarPayload {
  nome: string
  quantidade: number
  unidade: string
  valor_unitario: number
  validade: string | null
}

export type ItemAtualizarPayload = ItemCriarPayload
