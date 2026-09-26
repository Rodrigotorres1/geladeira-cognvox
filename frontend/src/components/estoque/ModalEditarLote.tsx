import { useState } from 'react'
import type { FormEvent } from 'react'
import { extrairMensagemErro } from '../../lib/erros'
import type { Lote, LoteAtualizarPayload } from '../../types/lote'
import { AcoesModal } from '../ui/AcoesModal'
import { Input } from '../ui/Input'
import { Modal } from '../ui/Modal'

interface ModalEditarLoteProps {
  lote: Lote
  onSalvar: (dados: LoteAtualizarPayload) => Promise<void>
  onFechar: () => void
}

// Quantidade não é editável aqui: correção de quantidade é entrada/saída com
// observação, para ficar registrada no histórico.
export function ModalEditarLote({ lote, onSalvar, onFechar }: ModalEditarLoteProps) {
  const [dataTeste, setDataTeste] = useState(lote.data_teste)
  const [numeroLote, setNumeroLote] = useState(lote.numero_lote ?? '')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function handleSubmit(evento: FormEvent) {
    evento.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      await onSalvar({ data_teste: dataTeste, numero_lote: numeroLote || null })
      onFechar()
    } catch (err) {
      setErro(extrairMensagemErro(err, 'Não foi possível salvar o lote.'))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal
      titulo="Editar lote"
      descricao={`${lote.tipo.nome} — ${lote.quantidade} em estoque`}
      onFechar={onFechar}
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          id="editar-data-teste"
          label="Data do teste"
          placeholder="04/2016, 4/2016 ou 2016"
          dica="Mês/ano ou só o ano"
          autoComplete="off"
          value={dataTeste}
          onChange={(e) => setDataTeste(e.target.value)}
          required
        />
        <Input
          id="editar-numero-lote"
          label="Nº do lote (opcional)"
          autoComplete="off"
          value={numeroLote}
          onChange={(e) => setNumeroLote(e.target.value)}
        />
        <p className="text-xs text-gray-500">
          Para corrigir a quantidade, registre uma entrada ou saída com observação.
        </p>
        <AcoesModal
          onCancelar={onFechar}
          enviando={enviando}
          textoEnviar="Salvar"
          textoEnviando="Salvando..."
          erro={erro}
        />
      </form>
    </Modal>
  )
}
