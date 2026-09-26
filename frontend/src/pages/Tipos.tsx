import { useState } from 'react'
import type { FormEvent } from 'react'
import { AcoesModal } from '../components/ui/AcoesModal'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { useTipos } from '../hooks/useTipos'
import { extrairMensagemErro } from '../lib/erros'
import { plural } from '../lib/formatos'
import type { TipoCilindro } from '../types/tipo'

interface FormularioTipo {
  nome: string
  estoque_minimo: string
  validade_anos: string
}

const FORMULARIO_VAZIO: FormularioTipo = { nome: '', estoque_minimo: '', validade_anos: '10' }

export function Tipos() {
  const { tipos, carregando, erro, criarTipo, atualizarTipo, removerTipo } = useTipos()

  const [formularioAberto, setFormularioAberto] = useState(false)
  const [tipoEditando, setTipoEditando] = useState<TipoCilindro | null>(null)
  const [formulario, setFormulario] = useState<FormularioTipo>(FORMULARIO_VAZIO)
  const [erroFormulario, setErroFormulario] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [erroAcao, setErroAcao] = useState<string | null>(null)

  function abrirNovoTipo() {
    setTipoEditando(null)
    setFormulario(FORMULARIO_VAZIO)
    setErroFormulario(null)
    setFormularioAberto(true)
  }

  function abrirEdicao(tipo: TipoCilindro) {
    setTipoEditando(tipo)
    setFormulario({
      nome: tipo.nome,
      estoque_minimo: String(tipo.estoque_minimo),
      validade_anos: String(tipo.validade_anos),
    })
    setErroFormulario(null)
    setFormularioAberto(true)
  }

  function fecharFormulario() {
    setFormularioAberto(false)
  }

  async function handleSubmit(evento: FormEvent) {
    evento.preventDefault()
    setErroFormulario(null)
    setEnviando(true)

    const dados = {
      nome: formulario.nome.trim(),
      estoque_minimo: Number(formulario.estoque_minimo),
      validade_anos: Number(formulario.validade_anos),
    }

    try {
      if (tipoEditando) {
        await atualizarTipo(tipoEditando.id, dados)
      } else {
        await criarTipo(dados)
      }
      setFormularioAberto(false)
    } catch (err) {
      setErroFormulario(extrairMensagemErro(err, 'Não foi possível salvar o tipo.'))
    } finally {
      setEnviando(false)
    }
  }

  async function handleRemover(tipo: TipoCilindro) {
    if (!window.confirm(`Excluir o tipo "${tipo.nome}"?`)) return
    setErroAcao(null)
    try {
      await removerTipo(tipo.id)
    } catch (err) {
      setErroAcao(extrairMensagemErro(err, `Não foi possível excluir "${tipo.nome}".`))
    }
  }

  return (
    <div className="flex flex-col gap-4 sm:gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-gray-900">Tipos de cilindro</h1>
        <Button onClick={abrirNovoTipo} className="w-full sm:w-auto">
          Novo tipo
        </Button>
      </div>

      {(erro || erroAcao) && (
        <p role="alert" className="text-sm font-medium text-red-600">
          {erro ?? erroAcao}
        </p>
      )}

      {carregando ? (
        <p className="text-gray-500">Carregando tipos...</p>
      ) : (
        <Card className="p-4 sm:p-6">
          {tipos.length === 0 ? (
            <p className="text-gray-500">Nenhum tipo cadastrado ainda.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {tipos.map((tipo) => (
                <li
                  key={tipo.id}
                  className="flex flex-col gap-3 py-3 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium text-gray-900">{tipo.nome}</p>
                      {tipo.estoque_baixo && <Badge cor="vermelho">Estoque baixo</Badge>}
                    </div>
                    <p className="mt-1 text-sm text-gray-600">
                      Mínimo {tipo.estoque_minimo} · validade do teste{' '}
                      {plural(tipo.validade_anos, 'ano', 'anos')} ·{' '}
                      {plural(tipo.estoque_disponivel, 'disponível', 'disponíveis')}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-2 sm:flex sm:shrink-0">
                    <Button variant="secondary" onClick={() => abrirEdicao(tipo)}>
                      Editar
                    </Button>
                    <Button variant="secondary" onClick={() => handleRemover(tipo)}>
                      Excluir
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {formularioAberto && (
        <Modal
          titulo={tipoEditando ? 'Editar tipo' : 'Novo tipo'}
          descricao={
            tipoEditando
              ? 'Mudar a validade recalcula o vencimento de todos os lotes deste tipo.'
              : undefined
          }
          onFechar={fecharFormulario}
        >
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              id="tipo-nome"
              label="Nome"
              placeholder="Ex.: Cilindro 10L"
              value={formulario.nome}
              onChange={(e) => setFormulario({ ...formulario, nome: e.target.value })}
              required
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                id="tipo-estoque-minimo"
                label="Estoque mínimo"
                type="number"
                inputMode="numeric"
                min="0"
                step="1"
                value={formulario.estoque_minimo}
                onChange={(e) => setFormulario({ ...formulario, estoque_minimo: e.target.value })}
                required
              />
              <Input
                id="tipo-validade"
                label="Validade (anos)"
                type="number"
                inputMode="numeric"
                min="1"
                step="1"
                dica="Do teste hidrostático"
                value={formulario.validade_anos}
                onChange={(e) => setFormulario({ ...formulario, validade_anos: e.target.value })}
                required
              />
            </div>
            <AcoesModal
              onCancelar={fecharFormulario}
              enviando={enviando}
              textoEnviar="Salvar"
              textoEnviando="Salvando..."
              erro={erroFormulario}
            />
          </form>
        </Modal>
      )}
    </div>
  )
}
