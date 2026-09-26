import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { useMovimentacoes } from '../hooks/useMovimentacoes'
import { formatarDataHora, plural } from '../lib/formatos'

export function Historico() {
  const { movimentacoes, carregando, erro } = useMovimentacoes()

  return (
    <div className="flex flex-col gap-4 sm:gap-6">
      <h1 className="text-xl font-semibold text-gray-900">Histórico</h1>

      {erro && <p className="text-sm font-medium text-red-600">{erro}</p>}

      {carregando ? (
        <p className="text-gray-500">Carregando histórico...</p>
      ) : (
        <Card className="p-4 sm:p-6">
          {movimentacoes.length === 0 ? (
            <p className="text-gray-500">Nenhuma movimentação registrada ainda.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {movimentacoes.map((mov) => (
                <li key={mov.id} className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0">
                  <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {mov.tipo === 'entrada' ? (
                        <Badge cor="verde">Entrada</Badge>
                      ) : (
                        <Badge cor="azul">Saída</Badge>
                      )}
                      <span className="font-medium text-gray-900">
                        {plural(mov.quantidade, 'cilindro', 'cilindros')} · {mov.lote.tipo.nome}
                      </span>
                    </div>
                    <time dateTime={mov.criado_em} className="text-xs text-gray-500">
                      {formatarDataHora(mov.criado_em)}
                    </time>
                  </div>
                  <p className="text-sm text-gray-600">
                    Teste {mov.lote.data_teste} · vence {mov.lote.vencimento}
                    {mov.lote.numero_lote && <> · lote {mov.lote.numero_lote}</>}
                  </p>
                  {mov.observacao && (
                    <p className="text-sm text-gray-500 italic">{mov.observacao}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}
    </div>
  )
}
