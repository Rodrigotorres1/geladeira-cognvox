import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CardTipo } from '../components/estoque/CardTipo'
import { ModalEditarLote } from '../components/estoque/ModalEditarLote'
import { ModalEntrada } from '../components/estoque/ModalEntrada'
import { ModalSaida } from '../components/estoque/ModalSaida'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useLotes } from '../hooks/useLotes'
import { useTipos } from '../hooks/useTipos'
import { loteParaSaida, plural } from '../lib/formatos'
import type { Lote, LoteAtualizarPayload } from '../types/lote'
import type { EntradaPayload, SaidaPayload } from '../types/movimentacao'

type ModalAberto =
  | { tipo: 'entrada'; tipoId: string }
  | { tipo: 'saida'; tipoId: string }
  | { tipo: 'editar'; lote: Lote }
  | null

export function Estoque() {
  const {
    tipos,
    carregando: carregandoTipos,
    erro: erroTipos,
    recarregar: recarregarTipos,
  } = useTipos()
  const {
    lotes,
    carregando: carregandoLotes,
    erro: erroLotes,
    registrarEntrada,
    registrarSaida,
    atualizarLote,
  } = useLotes()
  const [modal, setModal] = useState<ModalAberto>(null)

  const carregando = carregandoTipos || carregandoLotes
  const erro = erroTipos ?? erroLotes
  const tiposComLotes = tipos.filter((tipo) => lotes.some((lote) => lote.tipo.id === tipo.id))

  const lotesVencidos = lotes.filter((lote) => lote.status === 'vencido').length
  const lotesUrgentes = lotes.filter((lote) => lote.status === 'urgente').length
  const lotesAtencao = lotes.filter((lote) => lote.status === 'atencao').length
  const tiposEstoqueBaixo = tipos.filter((tipo) => tipo.estoque_baixo).length
  const temAlertas = lotesVencidos + lotesUrgentes + lotesAtencao + tiposEstoqueBaixo > 0

  function fecharModal() {
    setModal(null)
  }

  // Entrada/saída mudam o estoque disponível de cada tipo (calculado no
  // backend), então os tipos são recarregados junto com os lotes.
  async function handleEntrada(dados: EntradaPayload) {
    await registrarEntrada(dados)
    await recarregarTipos()
  }

  async function handleSaida(dados: SaidaPayload) {
    await registrarSaida(dados)
    await recarregarTipos()
  }

  // Mudar a data do teste pode fazer o lote vencer (ou deixar de vencer).
  async function handleEditarLote(id: string, dados: LoteAtualizarPayload) {
    await atualizarLote(id, dados)
    await recarregarTipos()
  }

  function abrirSaidaGeral() {
    const tipoId = loteParaSaida(lotes)?.tipo.id ?? tiposComLotes[0]?.id
    if (tipoId) setModal({ tipo: 'saida', tipoId })
  }

  if (carregando) {
    return <p className="text-gray-500">Carregando estoque...</p>
  }

  return (
    <div className="flex flex-col gap-4 sm:gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-gray-900">Estoque</h1>
        {tipos.length > 0 && (
          <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto">
            <Button onClick={() => setModal({ tipo: 'entrada', tipoId: tipos[0].id })}>
              Entrada
            </Button>
            <Button variant="secondary" onClick={abrirSaidaGeral} disabled={lotes.length === 0}>
              Saída
            </Button>
          </div>
        )}
      </div>

      {erro && <p className="text-sm font-medium text-red-600">{erro}</p>}

      {temAlertas && (
        <div className="flex flex-wrap gap-2" aria-label="Resumo dos alertas">
          {lotesVencidos > 0 && (
            <Badge cor="vermelho">{plural(lotesVencidos, 'lote vencido', 'lotes vencidos')}</Badge>
          )}
          {lotesUrgentes > 0 && (
            <Badge cor="laranja">{plural(lotesUrgentes, 'lote urgente', 'lotes urgentes')}</Badge>
          )}
          {lotesAtencao > 0 && (
            <Badge cor="amarelo">
              {plural(lotesAtencao, 'lote em atenção', 'lotes em atenção')}
            </Badge>
          )}
          {tiposEstoqueBaixo > 0 && (
            <Badge cor="vermelho">
              {plural(tiposEstoqueBaixo, 'tipo com estoque baixo', 'tipos com estoque baixo')}
            </Badge>
          )}
        </div>
      )}

      {tipos.length === 0 ? (
        <Card>
          <p className="text-gray-600">Nenhum tipo de cilindro cadastrado ainda.</p>
          <Link to="/tipos" className="mt-2 inline-block font-medium text-primary hover:underline">
            Cadastrar um tipo
          </Link>
        </Card>
      ) : (
        tipos.map((tipo) => (
          <CardTipo
            key={tipo.id}
            tipo={tipo}
            lotes={lotes.filter((lote) => lote.tipo.id === tipo.id)}
            onEntrada={() => setModal({ tipo: 'entrada', tipoId: tipo.id })}
            onSaida={() => setModal({ tipo: 'saida', tipoId: tipo.id })}
            onEditarLote={(lote) => setModal({ tipo: 'editar', lote })}
          />
        ))
      )}

      {modal?.tipo === 'entrada' && (
        <ModalEntrada
          tipos={tipos}
          tipoInicialId={modal.tipoId}
          onRegistrar={handleEntrada}
          onFechar={fecharModal}
        />
      )}

      {modal?.tipo === 'saida' && (
        <ModalSaida
          tipos={tiposComLotes}
          lotes={lotes}
          tipoInicialId={modal.tipoId}
          onRegistrar={handleSaida}
          onFechar={fecharModal}
        />
      )}

      {modal?.tipo === 'editar' && (
        <ModalEditarLote
          lote={modal.lote}
          onSalvar={(dados) => handleEditarLote(modal.lote.id, dados)}
          onFechar={fecharModal}
        />
      )}
    </div>
  )
}
