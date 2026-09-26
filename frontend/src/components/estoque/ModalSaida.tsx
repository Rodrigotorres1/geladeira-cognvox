import { useState } from 'react'
import type { FormEvent } from 'react'
import { extrairMensagemErro } from '../../lib/erros'
import { loteParaSaida } from '../../lib/formatos'
import type { Lote } from '../../types/lote'
import type { SaidaPayload } from '../../types/movimentacao'
import type { TipoCilindro } from '../../types/tipo'
import { StatusLote } from '../StatusLote'
import { AcoesModal } from '../ui/AcoesModal'
import { Input } from '../ui/Input'
import { Modal } from '../ui/Modal'
import { Select } from '../ui/Select'

interface ModalSaidaProps {
  // Só tipos que têm lote com estoque (sem lote não há de onde sair).
  tipos: TipoCilindro[]
  lotes: Lote[]
  tipoInicialId: string
  onRegistrar: (dados: SaidaPayload) => Promise<void>
  onFechar: () => void
}

function rotuloLote(lote: Lote) {
  const partes = [`Teste ${lote.data_teste}`, `vence ${lote.vencimento}`, `${lote.quantidade} disp.`]
  if (lote.numero_lote) partes.push(`lote ${lote.numero_lote}`)
  if (lote.status === 'vencido') partes.push('VENCIDO')
  return partes.join(' · ')
}

export function ModalSaida({ tipos, lotes, tipoInicialId, onRegistrar, onFechar }: ModalSaidaProps) {
  const [tipoId, setTipoId] = useState(tipoInicialId)
  const lotesDoTipo = lotes.filter((lote) => lote.tipo.id === tipoId)
  const [loteId, setLoteId] = useState(() => loteParaSaida(lotesDoTipo)?.id ?? '')
  const [quantidade, setQuantidade] = useState('')
  const [observacao, setObservacao] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const loteSelecionado = lotesDoTipo.find((lote) => lote.id === loteId)

  function trocarTipo(novoTipoId: string) {
    setTipoId(novoTipoId)
    // Ao trocar o tipo, pré-seleciona de novo o lote que vence primeiro.
    const doNovoTipo = lotes.filter((lote) => lote.tipo.id === novoTipoId)
    setLoteId(loteParaSaida(doNovoTipo)?.id ?? '')
  }

  async function handleSubmit(evento: FormEvent) {
    evento.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      await onRegistrar({
        lote_id: loteId,
        quantidade: Number(quantidade),
        observacao: observacao || null,
      })
      onFechar()
    } catch (err) {
      setErro(extrairMensagemErro(err, 'Não foi possível registrar a saída.'))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal
      titulo="Registrar saída"
      descricao="Já vem selecionado o lote que vence primeiro."
      onFechar={onFechar}
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Select
          id="saida-tipo"
          label="Tipo de cilindro"
          value={tipoId}
          onChange={(e) => trocarTipo(e.target.value)}
          required
        >
          {tipos.map((tipo) => (
            <option key={tipo.id} value={tipo.id}>
              {tipo.nome}
            </option>
          ))}
        </Select>
        <div className="flex flex-col gap-2">
          <Select
            id="saida-lote"
            label="Lote"
            value={loteId}
            onChange={(e) => setLoteId(e.target.value)}
            required
          >
            {lotesDoTipo.map((lote) => (
              <option key={lote.id} value={lote.id}>
                {rotuloLote(lote)}
              </option>
            ))}
          </Select>
          {loteSelecionado && <StatusLote lote={loteSelecionado} />}
        </div>
        <Input
          id="saida-quantidade"
          label="Quantidade"
          type="number"
          inputMode="numeric"
          min="1"
          step="1"
          max={loteSelecionado?.quantidade}
          dica={loteSelecionado ? `Disponível neste lote: ${loteSelecionado.quantidade}` : undefined}
          value={quantidade}
          onChange={(e) => setQuantidade(e.target.value)}
          required
          autoFocus
        />
        <Input
          id="saida-observacao"
          label="Observação (opcional)"
          placeholder="Ex.: paciente, reteste, descarte"
          value={observacao}
          onChange={(e) => setObservacao(e.target.value)}
        />
        <AcoesModal
          onCancelar={onFechar}
          enviando={enviando}
          textoEnviar="Registrar saída"
          textoEnviando="Registrando..."
          erro={erro}
        />
      </form>
    </Modal>
  )
}
