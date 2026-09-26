import { forwardRef } from 'react'
import type { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  // Texto de ajuda fixo abaixo do campo (o placeholder some quando o campo
  // já vem preenchido).
  dica?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, dica, id, className = '', ...props },
  ref,
) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      {/* text-base no celular: o Safari do iPhone dá zoom na página ao focar
          um campo com fonte menor que 16px. */}
      <input
        id={id}
        ref={ref}
        className={`rounded-md border border-gray-300 px-3 py-2 text-base text-gray-900 placeholder:text-gray-400 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none sm:text-sm ${className}`}
        {...props}
      />
      {dica && <p className="text-xs text-gray-500">{dica}</p>}
    </div>
  )
})
