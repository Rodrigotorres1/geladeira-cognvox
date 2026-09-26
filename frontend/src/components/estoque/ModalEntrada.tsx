import { useState } from 'react'
import type { FormEvent } from 'react'
import { extrairMensagemErro } from '../../lib/erros'
import { mesAnoAtual } from '../../lib/formatos'
import type { EntradaPayload } from '../../types/movimentacao'
import type { TipoCilindro } from '../../types/tipo'
import { AcoesModal } from '../ui/AcoesModal'
import { Input } from '../ui/Input'
import { Modal } from '../ui/Modal'
import { Select } from '../ui/Select'

interface ModalEntradaProps {
  tipos: TipoCilindro[]
  tipoInicialId: string
  onRegistrar: (dados: EntradaPayload) => Promise<void>
  onFechar: () => void
}

export function ModalEntrada({ tipos, tipoInicialId, onRegistrar, onFechar }: ModalEntradaProps) {
  const [tipoId, setTipoId] = useState(tipoInicialId)
  // Vem preenchido com o mês atual: cilindro recém-testado é o caso comum.
  const [dataTeste, setDataTeste] = useState(mesAnoAtual)
  const [quantidade, setQuantidade] = useState('')
  const [numeroLote, setNumeroLote] = useState('')
  const [observacao, setObservacao] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function handleSubmit(evento: FormEvent) {
    evento.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      await onRegistrar({
        tipo_id: tipoId,
        data_teste: dataTeste,
        quantidade: Number(quantidade),
        numero_lote: numeroLote || null,
        observacao: observacao || null,
      })
      onFechar()
    } catch (err) {
      setErro(extrairMensagemErro(err, 'Não foi possível registrar a entrada.'))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal
      titulo="Registrar entrada"
      descricao="Mesmo tipo e mesma data do teste somam no lote que já existe."
      onFechar={onFechar}
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Select
          id="entrada-tipo"
          label="Tipo de cilindro"
          value={tipoId}
          onChange={(e) => setTipoId(e.target.value)}
          required
        >
          {tipos.map((tipo) => (
            <option key={tipo.id} value={tipo.id}>
              {tipo.nome}
            </option>
          ))}
        </Select>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            id="entrada-data-teste"
            label="Data do teste"
            placeholder="04/2016, 4/2016 ou 2016"
            dica="Mês/ano ou só o ano"
            autoComplete="off"
            value={dataTeste}
            onChange={(e) => setDataTeste(e.target.value)}
            required
          />
          <Input
            id="entrada-quantidade"
            label="Quantidade"
            type="number"
            inputMode="numeric"
            min="1"
            step="1"
            value={quantidade}
            onChange={(e) => setQuantidade(e.target.value)}
            required
            autoFocus
          />
        </div>
        <Input
          id="entrada-numero-lote"
          label="Nº do lote (opcional)"
          autoComplete="off"
          value={numeroLote}
          onChange={(e) => setNumeroLote(e.target.value)}
        />
        <Input
          id="entrada-observacao"
          label="Observação (opcional)"
          value={observacao}
          onChange={(e) => setObservacao(e.target.value)}
        />
        <AcoesModal
          onCancelar={onFechar}
          enviando={enviando}
          textoEnviar="Registrar entrada"
          textoEnviando="Registrando..."
          erro={erro}
        />
      </form>
    </Modal>
  )
}
