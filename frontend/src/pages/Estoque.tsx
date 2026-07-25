import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { useItens } from '../hooks/useItens'
import { extrairMensagemErro } from '../lib/erros'
import type { ItemCriarPayload, ItemEstoque } from '../types/item'

interface FormularioItem {
  nome: string
  quantidade: string
  unidade: string
  valor_unitario: string
  validade: string
}

const FORMULARIO_VAZIO: FormularioItem = {
  nome: '',
  quantidade: '',
  unidade: '',
  valor_unitario: '',
  validade: '',
}

function formatarData(data: string | null) {
  if (!data) return '-'
  // Split manual em vez de `new Date(data)`: uma string "YYYY-MM-DD" é
  // interpretada como meia-noite UTC, o que pode "voltar" um dia ao converter
  // para o fuso local. Formatando os componentes direto, isso não acontece.
  const [ano, mes, dia] = data.split('-')
  return `${dia}/${mes}/${ano}`
}

const LIMITE_ESTOQUE_BAIXO = 3
const DIAS_ALERTA_VALIDADE = 7

// "YYYY-MM-DD" comparado como string já dá a ordem cronológica certa (zero
// à esquerda garante isso), então nem precisa converter para Date — mesmo
// raciocínio de formatarData: evitar `new Date(stringISO)` e seu bug de fuso.
function dataISO(data: Date) {
  const ano = data.getFullYear()
  const mes = String(data.getMonth() + 1).padStart(2, '0')
  const dia = String(data.getDate()).padStart(2, '0')
  return `${ano}-${mes}-${dia}`
}

function estoqueBaixo(item: ItemEstoque) {
  return item.quantidade < LIMITE_ESTOQUE_BAIXO
}

function validadeVencida(item: ItemEstoque) {
  return item.validade !== null && item.validade < dataISO(new Date())
}

function validadeProxima(item: ItemEstoque) {
  if (item.validade === null) return false
  const limite = new Date()
  limite.setDate(limite.getDate() + DIAS_ALERTA_VALIDADE)
  return item.validade >= dataISO(new Date()) && item.validade <= dataISO(limite)
}

export function Estoque() {
  const { itens, carregando, erro, criarItem, atualizarItem, removerItem, registrarEntrada } =
    useItens()

  const [formularioAberto, setFormularioAberto] = useState(false)
  const [itemEditando, setItemEditando] = useState<ItemEstoque | null>(null)
  const [formulario, setFormulario] = useState<FormularioItem>(FORMULARIO_VAZIO)
  const [erroFormulario, setErroFormulario] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [erroAcao, setErroAcao] = useState<string | null>(null)

  const [itemEntrada, setItemEntrada] = useState<ItemEstoque | null>(null)
  const [quantidadeEntrada, setQuantidadeEntrada] = useState('')
  const [erroEntrada, setErroEntrada] = useState<string | null>(null)
  const [enviandoEntrada, setEnviandoEntrada] = useState(false)

  function abrirNovoItem() {
    setItemEditando(null)
    setFormulario(FORMULARIO_VAZIO)
    setErroFormulario(null)
    setFormularioAberto(true)
  }

  function abrirEdicaoItem(item: ItemEstoque) {
    setItemEditando(item)
    setFormulario({
      nome: item.nome,
      quantidade: String(item.quantidade),
      unidade: item.unidade,
      valor_unitario: item.valor_unitario,
      validade: item.validade ?? '',
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

    const dados: ItemCriarPayload = {
      nome: formulario.nome,
      quantidade: Number(formulario.quantidade),
      unidade: formulario.unidade,
      valor_unitario: Number(formulario.valor_unitario),
      validade: formulario.validade || null,
    }

    try {
      if (itemEditando) {
        await atualizarItem(itemEditando.id, dados)
      } else {
        await criarItem(dados)
      }
      setFormularioAberto(false)
    } catch {
      setErroFormulario('Não foi possível salvar o item. Confira os dados informados.')
    } finally {
      setEnviando(false)
    }
  }

  async function handleRemover(item: ItemEstoque) {
    if (!window.confirm(`Remover "${item.nome}" do estoque?`)) return
    setErroAcao(null)
    try {
      await removerItem(item.id)
    } catch {
      setErroAcao(`Não foi possível remover "${item.nome}".`)
    }
  }

  function abrirEntrada(item: ItemEstoque) {
    setItemEntrada(item)
    setQuantidadeEntrada('')
    setErroEntrada(null)
  }

  function fecharEntrada() {
    setItemEntrada(null)
  }

  async function handleSubmitEntrada(evento: FormEvent) {
    evento.preventDefault()
    if (!itemEntrada) return
    setErroEntrada(null)
    setEnviandoEntrada(true)
    try {
      await registrarEntrada(itemEntrada.id, Number(quantidadeEntrada))
      setItemEntrada(null)
    } catch (err) {
      setErroEntrada(extrairMensagemErro(err, 'Não foi possível registrar a entrada.'))
    } finally {
      setEnviandoEntrada(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Estoque</h1>
        <Button onClick={abrirNovoItem}>Novo item</Button>
      </div>

      {(erro || erroAcao) && (
        <p className="text-sm font-medium text-red-600">{erro ?? erroAcao}</p>
      )}

      {carregando ? (
        <p className="text-gray-500">Carregando itens...</p>
      ) : (
        <Card>
          {itens.length === 0 ? (
            <p className="text-gray-500">Nenhum item cadastrado ainda.</p>
          ) : (
            <div className="overflow-x-auto">
              {itens.some((item) => estoqueBaixo(item) || validadeProxima(item) || validadeVencida(item)) && (
                <p className="mb-3 text-xs text-gray-500">
                  <span className="font-semibold text-orange-600">Laranja</span>: estoque abaixo
                  de {LIMITE_ESTOQUE_BAIXO} ou validade nos próximos {DIAS_ALERTA_VALIDADE} dias ·{' '}
                  <span className="font-semibold text-red-600">Vermelho</span>: item vencido
                </p>
              )}
              <table className="w-full text-left text-sm">
                <thead className="border-b border-gray-200 text-gray-600">
                  <tr>
                    <th className="py-2 pr-4 font-medium">Nome</th>
                    <th className="py-2 pr-4 font-medium">Quantidade</th>
                    <th className="py-2 pr-4 font-medium">Unidade</th>
                    <th className="py-2 pr-4 font-medium">Valor unitário</th>
                    <th className="py-2 pr-4 font-medium">Validade</th>
                    <th className="py-2 pr-0 font-medium"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {itens.map((item) => {
                    const vencido = validadeVencida(item)
                    const proxima = !vencido && validadeProxima(item)
                    const baixo = estoqueBaixo(item)
                    const destaque = vencido
                      ? 'border-l-4 border-red-500 bg-red-50'
                      : baixo || proxima
                        ? 'border-l-4 border-orange-400 bg-orange-50'
                        : ''

                    return (
                      <tr key={item.id} className={destaque}>
                        <td className="py-3 pr-4 pl-2 text-gray-900">{item.nome}</td>
                        <td
                          className={`py-3 pr-4 ${baixo ? 'font-semibold text-orange-600' : 'text-gray-600'}`}
                        >
                          {item.quantidade}
                          {baixo && <span className="ml-1 text-xs font-normal">(baixo)</span>}
                        </td>
                        <td className="py-3 pr-4 text-gray-600">{item.unidade}</td>
                        <td className="py-3 pr-4 text-gray-600">
                          R$ {Number(item.valor_unitario).toFixed(2)}
                        </td>
                        <td
                          className={`py-3 pr-4 ${
                            vencido
                              ? 'font-semibold text-red-600'
                              : proxima
                                ? 'font-semibold text-orange-600'
                                : 'text-gray-600'
                          }`}
                        >
                          {formatarData(item.validade)}
                          {vencido && <span className="ml-1 text-xs font-normal">(vencido)</span>}
                          {proxima && (
                            <span className="ml-1 text-xs font-normal">(vence em breve)</span>
                          )}
                        </td>
                        <td className="py-3 pr-0">
                          <div className="flex justify-end gap-2">
                            <Button variant="secondary" onClick={() => abrirEntrada(item)}>
                              Entrada
                            </Button>
                            <Button variant="secondary" onClick={() => abrirEdicaoItem(item)}>
                              Editar
                            </Button>
                            <Button variant="secondary" onClick={() => handleRemover(item)}>
                              Remover
                            </Button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {formularioAberto && (
        <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/40 px-4">
          <Card className="w-full max-w-md">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">
              {itemEditando ? 'Editar item' : 'Novo item'}
            </h2>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <Input
                id="nome"
                label="Nome"
                value={formulario.nome}
                onChange={(e) => setFormulario({ ...formulario, nome: e.target.value })}
                required
              />
              <div className="grid grid-cols-2 gap-4">
                <Input
                  id="quantidade"
                  label="Quantidade"
                  type="number"
                  min="0"
                  step="any"
                  value={formulario.quantidade}
                  onChange={(e) => setFormulario({ ...formulario, quantidade: e.target.value })}
                  required
                />
                <Input
                  id="unidade"
                  label="Unidade"
                  placeholder="un, litro, kg..."
                  value={formulario.unidade}
                  onChange={(e) => setFormulario({ ...formulario, unidade: e.target.value })}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  id="valor_unitario"
                  label="Valor unitário"
                  type="number"
                  min="0"
                  step="0.01"
                  value={formulario.valor_unitario}
                  onChange={(e) =>
                    setFormulario({ ...formulario, valor_unitario: e.target.value })
                  }
                  required
                />
                <Input
                  id="validade"
                  label="Validade (opcional)"
                  type="date"
                  value={formulario.validade}
                  onChange={(e) => setFormulario({ ...formulario, validade: e.target.value })}
                />
              </div>
              {erroFormulario && (
                <p className="text-sm font-medium text-red-600">{erroFormulario}</p>
              )}
              <div className="mt-2 flex justify-end gap-3">
                <Button type="button" variant="secondary" onClick={fecharFormulario}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={enviando}>
                  {enviando ? 'Salvando...' : 'Salvar'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {itemEntrada && (
        <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/40 px-4">
          <Card className="w-full max-w-sm">
            <h2 className="mb-1 text-lg font-semibold text-gray-900">Registrar entrada</h2>
            <p className="mb-4 text-sm text-gray-600">
              {itemEntrada.nome} — {itemEntrada.quantidade} {itemEntrada.unidade} em estoque
            </p>
            <form onSubmit={handleSubmitEntrada} className="flex flex-col gap-4">
              <Input
                id="quantidade-entrada"
                label="Quantidade a adicionar"
                type="number"
                min="0"
                step="any"
                value={quantidadeEntrada}
                onChange={(e) => setQuantidadeEntrada(e.target.value)}
                required
                autoFocus
              />
              {erroEntrada && <p className="text-sm font-medium text-red-600">{erroEntrada}</p>}
              <div className="mt-2 flex justify-end gap-3">
                <Button type="button" variant="secondary" onClick={fecharEntrada}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={enviandoEntrada}>
                  {enviandoEntrada ? 'Registrando...' : 'Registrar entrada'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
