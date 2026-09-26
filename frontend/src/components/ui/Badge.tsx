import type { ReactNode } from 'react'

export type CorBadge = 'neutro' | 'amarelo' | 'laranja' | 'vermelho' | 'verde' | 'azul'

const classesCor: Record<CorBadge, string> = {
  neutro: 'bg-gray-100 text-gray-700',
  amarelo: 'bg-yellow-100 text-yellow-800',
  laranja: 'bg-orange-100 text-orange-800',
  vermelho: 'bg-red-100 text-red-700',
  verde: 'bg-green-100 text-green-800',
  azul: 'bg-blue-100 text-blue-800',
}

export function Badge({ cor = 'neutro', children }: { cor?: CorBadge; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold whitespace-nowrap ${classesCor[cor]}`}
    >
      {children}
    </span>
  )
}
