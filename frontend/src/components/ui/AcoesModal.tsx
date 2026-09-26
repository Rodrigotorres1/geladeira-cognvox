import { Button } from './Button'

interface AcoesModalProps {
  onCancelar: () => void
  enviando: boolean
  textoEnviar: string
  textoEnviando: string
  erro?: string | null
}

// Rodapé padrão dos formulários em modal: mensagem de erro + Cancelar/Enviar.
// No celular os botões ocupam a largura toda, com a ação principal em cima.
export function AcoesModal({
  onCancelar,
  enviando,
  textoEnviar,
  textoEnviando,
  erro,
}: AcoesModalProps) {
  return (
    <>
      {erro && (
        <p role="alert" className="text-sm font-medium text-red-600">
          {erro}
        </p>
      )}
      <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end sm:gap-3">
        <Button type="button" variant="secondary" onClick={onCancelar} className="w-full sm:w-auto">
          Cancelar
        </Button>
        <Button type="submit" disabled={enviando} className="w-full sm:w-auto">
          {enviando ? textoEnviando : textoEnviar}
        </Button>
      </div>
    </>
  )
}
