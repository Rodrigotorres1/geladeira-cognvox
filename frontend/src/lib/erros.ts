import axios from 'axios'

// O FastAPI devolve `detail` em dois formatos: texto (erros de regra, ex.:
// 409/400/404) ou lista de erros por campo (422 de validação do Pydantic,
// ex.: data do teste inválida). Na lista, mostra a mensagem do primeiro campo.
export function extrairMensagemErro(erro: unknown, mensagemPadrao: string) {
  if (!axios.isAxiosError(erro)) return mensagemPadrao

  const detail: unknown = erro.response?.data?.detail
  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    const primeiro: unknown = detail[0]
    if (
      typeof primeiro === 'object' &&
      primeiro !== null &&
      'msg' in primeiro &&
      typeof primeiro.msg === 'string'
    ) {
      return primeiro.msg
    }
  }

  return mensagemPadrao
}
