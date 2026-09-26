import { plural } from '../../lib/formatos'
import type { Lote, StatusLote as Status } from '../../types/lote'
import type { TipoCilindro } from '../../types/tipo'
import { StatusLote } from '../StatusLote'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

interface CardTipoProps {
  tipo: TipoCilindro
  // Lotes deste tipo com estoque, já na ordem de vencimento da API.
  lotes: Lote[]
  onEntrada: () => void
  onSaida: () => void
  onEditarLote: (lote: Lote) => void
}

const bordaPorStatus: Record<Status, string> = {
  ok: 'border-transparent',
  atencao: 'border-yellow-400',
  urgente: 'border-orange-400',
  vencido: 'border-red-500',
}

export function CardTipo({ tipo, lotes, onEntrada, onSaida, onEditarLote }: CardTipoProps) {
  const vencidos = lotes
    .filter((lote) => lote.status === 'vencido')
    .reduce((total, lote) => total + lote.quantidade, 0)

  return (
    <Card className="p-4 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-900">{tipo.nome}</h2>
            {tipo.estoque_baixo && <Badge cor="vermelho">Estoque baixo</Badge>}
          </div>
          <p className="mt-1 text-sm text-gray-600">
            <span className="font-semibold text-gray-900">
              {plural(tipo.estoque_disponivel, 'disponível', 'disponíveis')}
            </span>{' '}
            · mínimo {tipo.estoque_minimo}
            {vencidos > 0 && (
              <span className="text-red-700"> · {plural(vencidos, 'vencido', 'vencidos')}</span>
            )}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:flex sm:shrink-0">
          <Button onClick={onEntrada}>Entrada</Button>
          <Button variant="secondary" onClick={onSaida} disabled={lotes.length === 0}>
            Saída
          </Button>
        </div>
      </div>

      {lotes.length === 0 ? (
        <p className="mt-4 text-sm text-gray-500">Nenhum cilindro em estoque.</p>
      ) : (
        <ul className="mt-4 divide-y divide-gray-100 border-t border-gray-100">
          {lotes.map((lote) => (
            <li
              key={lote.id}
              className={`flex items-start justify-between gap-3 border-l-4 py-3 pl-3 ${bordaPorStatus[lote.status]}`}
            >
              <div className="flex min-w-0 flex-col gap-1">
                <p className="text-sm font-medium text-gray-900">
                  {plural(lote.quantidade, 'cilindro', 'cilindros')}
                  {lote.numero_lote && (
                    <span className="font-normal text-gray-500"> · lote {lote.numero_lote}</span>
                  )}
                </p>
                <p className="text-sm text-gray-600">
                  Teste {lote.data_teste} · vence {lote.vencimento}
                </p>
                <StatusLote lote={lote} />
              </div>
              <Button variant="secondary" onClick={() => onEditarLote(lote)} className="shrink-0">
                Editar
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
