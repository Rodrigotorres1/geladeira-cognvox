export interface TipoResumo {
  id: string
  nome: string
}

export interface TipoCilindro {
  id: string
  nome: string
  estoque_minimo: number
  validade_anos: number
  criado_em: string
  // Calculados no backend: estoque_disponivel já ignora lotes vencidos.
  estoque_disponivel: number
  estoque_baixo: boolean
}

export interface TipoPayload {
  nome: string
  estoque_minimo: number
  validade_anos: number
}
