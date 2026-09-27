"""Cliente HTTP do módulo proxy/cache de câmbio.

O back-end principal nunca fala direto com a API externa: todas as
cotações passam pelo serviço em cambio/ (Front → Back → Proxy/Cache → API).
"""
import requests
from config import CAMBIO_SERVICE_URL, CAMBIO_TIMEOUT_SEGUNDOS


class CambioError(Exception):
    """Falha ao obter uma cotação. `status` é o código HTTP sugerido para
    devolver ao front e `mensagem` é o texto para mostrar ao usuário."""

    def __init__(self, mensagem, status):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def buscar_cotacao(moeda, data=None):
    """Consulta o módulo de câmbio.

    Com `data` (AAAA-MM-DD) retorna a cotação daquele dia; sem `data`,
    a cotação atual. Retorna o JSON do módulo, ex:
    {"moeda": "USD", "data": "2026-08-15", "data_cotacao": "2026-08-14", "valor": 5.43, ...}

    Lança CambioError com uma mensagem clara em qualquer falha.
    """
    parametros = {"moeda": moeda}
    if data:
        parametros["data"] = data

    try:
        resposta = requests.get(
            f"{CAMBIO_SERVICE_URL}/cotacao", params=parametros, timeout=CAMBIO_TIMEOUT_SEGUNDOS
        )
    except requests.RequestException:
        raise CambioError(
            "O serviço de câmbio está indisponível no momento. Tente novamente mais tarde.", 503
        )

    try:
        corpo = resposta.json()
    except ValueError:
        corpo = {}

    if resposta.status_code != 200:
        mensagem = corpo.get("erro") or "Não foi possível obter a cotação."
        # 400/404 são erros do pedido (moeda/data); o resto vira 502
        status = resposta.status_code if resposta.status_code in (400, 404) else 502
        raise CambioError(mensagem, status)

    if "valor" not in corpo:
        raise CambioError("Resposta inválida do serviço de câmbio.", 502)

    return corpo
