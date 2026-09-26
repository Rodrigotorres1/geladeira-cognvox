import type { Lote } from '../types/lote'

export function plural(quantidade: number, singular: string, pluralTexto: string) {
  return `${quantidade} ${quantidade === 1 ? singular : pluralTexto}`
}

// Valor inicial do campo "data do teste" no modal de entrada.
export function mesAnoAtual() {
  const hoje = new Date()
  return `${String(hoje.getMonth() + 1).padStart(2, '0')}/${hoje.getFullYear()}`
}

// Até 12 meses: "5 meses". Acima disso: "3 anos e 4 meses" (ou só "2 anos").
export function formatarDuracaoMeses(meses: number) {
  if (meses <= 12) return plural(meses, 'mês', 'meses')
  const anos = Math.floor(meses / 12)
  const resto = meses % 12
  const textoAnos = plural(anos, 'ano', 'anos')
  return resto === 0 ? textoAnos : `${textoAnos} e ${plural(resto, 'mês', 'meses')}`
}

export function descreverMesesRestantes(meses: number) {
  if (meses < 0) return `vencido há ${formatarDuracaoMeses(-meses)}`
  if (meses === 0) return 'vence este mês'
  return `vence em ${formatarDuracaoMeses(meses)}`
}

// O backend grava criado_em em UTC sem indicar o fuso ("2026-09-26T21:32:08").
// Sem o "Z", o navegador interpretaria como hora local e mostraria 3h a mais.
export function formatarDataHora(iso: string) {
  const temFuso = /(Z|[+-]\d{2}:?\d{2})$/.test(iso)
  return new Date(temFuso ? iso : `${iso}Z`).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Lote pré-selecionado na saída: a API já devolve os lotes ordenados por
// vencimento, então é o primeiro não vencido (ou o primeiro vencido, se só
// sobrarem vencidos).
export function loteParaSaida(lotes: Lote[]) {
  return lotes.find((lote) => lote.status !== 'vencido') ?? lotes[0]
}
