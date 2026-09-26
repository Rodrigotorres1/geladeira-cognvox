import { useEffect, useId } from 'react'
import type { ReactNode } from 'react'

interface ModalProps {
  titulo: string
  descricao?: ReactNode
  onFechar: () => void
  children: ReactNode
}

// No celular abre como "folha" presa embaixo da tela (mais fácil de alcançar
// com o polegar); a partir de sm vira o modal centralizado de sempre.
export function Modal({ titulo, descricao, onFechar, children }: ModalProps) {
  const idTitulo = useId()

  useEffect(() => {
    function fecharComEsc(evento: KeyboardEvent) {
      if (evento.key === 'Escape') onFechar()
    }
    window.addEventListener('keydown', fecharComEsc)
    return () => window.removeEventListener('keydown', fecharComEsc)
  }, [onFechar])

  return (
    <div className="fixed inset-0 z-10 flex items-end justify-center bg-black/40 sm:items-center sm:px-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        className="max-h-[90dvh] w-full overflow-y-auto rounded-t-xl bg-white p-5 shadow-lg sm:max-w-md sm:rounded-lg sm:p-6"
      >
        <h2 id={idTitulo} className="text-lg font-semibold text-gray-900">
          {titulo}
        </h2>
        {descricao && <div className="mt-1 text-sm text-gray-600">{descricao}</div>}
        <div className="mt-4">{children}</div>
      </div>
    </div>
  )
}
