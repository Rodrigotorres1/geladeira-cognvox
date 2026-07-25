import axios from 'axios'

export function extrairMensagemErro(erro: unknown, mensagemPadrao: string) {
  if (axios.isAxiosError(erro) && typeof erro.response?.data?.detail === 'string') {
    return erro.response.data.detail as string
  }
  return mensagemPadrao
}
