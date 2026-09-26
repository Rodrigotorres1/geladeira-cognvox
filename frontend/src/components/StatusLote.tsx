import { descreverMesesRestantes } from '../lib/formatos'
import type { Lote, StatusLote as Status } from '../types/lote'
import { Badge } from './ui/Badge'
import type { CorBadge } from './ui/Badge'

// "ok" não tem badge: só o texto "vence em X meses", para os alertas
// chamarem atenção por contraste.
const badgePorStatus: Record<Exclude<Status, 'ok'>, { cor: CorBadge; texto: string }> = {
  atencao: { cor: 'amarelo', texto: 'Atenção' },
  urgente: { cor: 'laranja', texto: 'Urgente' },
  vencido: { cor: 'vermelho', texto: 'Vencido' },
}

export function StatusLote({ lote }: { lote: Pick<Lote, 'status' | 'meses_restantes'> }) {
  const badge = lote.status === 'ok' ? null : badgePorStatus[lote.status]

  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      {badge && <Badge cor={badge.cor}>{badge.texto}</Badge>}
      <span className={`text-sm ${lote.status === 'vencido' ? 'text-red-700' : 'text-gray-600'}`}>
        {descreverMesesRestantes(lote.meses_restantes)}
      </span>
    </span>
  )
}
