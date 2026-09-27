import requests
from config import AWESOME_API_BASE_URL


def buscar_cotacao_historica(moeda, data_iso):
    """Busca a cotação de fechamento de `moeda` (ex: USD) contra o BRL
    na data `data_iso` (formato 'AAAA-MM-DD').

    Retorna {"valor": float, "data": "AAAA-MM-DD"} ou None se não houver
    pregão nessa data (fim de semana/feriado).
    """
    data_formatada = data_iso.replace("-", "")
    url = (
        f"{AWESOME_API_BASE_URL}/json/daily/{moeda}-BRL/"
        f"?start_date={data_formatada}&end_date={data_formatada}"
    )
    resposta = requests.get(url, timeout=10)
    resposta.raise_for_status()
    dados = resposta.json()

    if not dados:
        return None

    item = dados[0]
    return {"valor": float(item["bid"]), "data": data_iso}


def buscar_cotacao_atual(moeda):
    """Busca a cotação mais recente de `moeda` contra o BRL.

    Retorna {"valor": float, "data": "AAAA-MM-DD"}.
    """
    url = f"{AWESOME_API_BASE_URL}/json/last/{moeda}-BRL"
    resposta = requests.get(url, timeout=10)
    resposta.raise_for_status()
    dados = resposta.json()

    item = dados[f"{moeda}BRL"]
    return {"valor": float(item["bid"]), "data": item["create_date"][:10]}
