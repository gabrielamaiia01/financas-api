from datetime import date, timedelta

import pytest
import requests

import cliente_cambio


class RespostaFalsa:
    def __init__(self, status_code, corpo):
        self.status_code = status_code
        self._corpo = corpo

    def json(self):
        return self._corpo


@pytest.fixture
def proxy(monkeypatch):
    """Simula o módulo de câmbio. `respostas` mapeia a data (ou None p/ atual)
    para uma RespostaFalsa ou exceção."""
    estado = {"respostas": {}, "chamadas": []}

    def get(url, params, timeout):
        estado["chamadas"].append((url, params))
        resposta = estado["respostas"][params.get("data")]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    monkeypatch.setattr(cliente_cambio.requests, "get", get)
    return estado


TRANSACAO = {"descricao": "Hotel", "valor": 100, "moeda": "USD", "data": "2026-08-14"}


def test_criar_transacao_preenche_cotacao(client, proxy):
    proxy["respostas"]["2026-08-14"] = RespostaFalsa(200, {"valor": 5.43})

    r = client.post("/transacoes", json=TRANSACAO)

    assert r.status_code == 201
    assert r.json["cotacao_utilizada"] == 5.43
    assert r.json["valor_convertido_brl"] == 543.0
    url, params = proxy["chamadas"][0]
    assert url.endswith("/cotacao") and params == {"moeda": "USD", "data": "2026-08-14"}


def test_transacao_em_brl_nao_chama_proxy(client, proxy):
    r = client.post("/transacoes", json={**TRANSACAO, "moeda": "brl"})
    assert r.status_code == 201
    assert r.json["cotacao_utilizada"] == 1.0
    assert r.json["valor_convertido_brl"] == 100.0
    assert proxy["chamadas"] == []


def test_data_futura(client, proxy):
    amanha = (date.today() + timedelta(days=1)).isoformat()
    r = client.post("/transacoes", json={**TRANSACAO, "data": amanha})
    assert r.status_code == 400
    assert "futuro" in r.json["erro"]


def test_moeda_invalida_repassa_mensagem_do_proxy(client, proxy):
    proxy["respostas"]["2026-08-14"] = RespostaFalsa(
        400, {"erro": "Moeda 'XYZ' não é suportada pela API de câmbio."}
    )
    r = client.post("/transacoes", json={**TRANSACAO, "moeda": "XYZ"})
    assert r.status_code == 400
    assert "XYZ" in r.json["erro"]
    assert client.get("/transacoes").json == []


def test_api_externa_fora_do_ar(client, proxy):
    proxy["respostas"]["2026-08-14"] = RespostaFalsa(
        502, {"erro": "Não foi possível consultar a API externa de câmbio."}
    )
    r = client.post("/transacoes", json=TRANSACAO)
    assert r.status_code == 502


def test_proxy_fora_do_ar(client, proxy):
    proxy["respostas"]["2026-08-14"] = requests.ConnectionError("recusada")
    r = client.post("/transacoes", json=TRANSACAO)
    assert r.status_code == 503
    assert "indisponível" in r.json["erro"]


def test_campos_obrigatorios(client, proxy):
    r = client.post("/transacoes", json={"valor": 10})
    assert r.status_code == 400


def test_comparar(client, proxy):
    proxy["respostas"]["2026-08-14"] = RespostaFalsa(200, {"valor": 5.0})
    proxy["respostas"][None] = RespostaFalsa(200, {"valor": 5.5, "data": "2026-09-25"})
    transacao_id = client.post("/transacoes", json=TRANSACAO).json["id"]

    r = client.get(f"/transacoes/{transacao_id}/comparar")

    assert r.status_code == 200
    assert r.json["cotacao_utilizada"] == 5.0
    assert r.json["cotacao_atual"] == 5.5
    assert r.json["variacao_percentual"] == 10.0
    assert r.json["valor_hoje_brl"] == 550.0
    assert r.json["diferenca_brl"] == 50.0
    assert proxy["chamadas"][-1][1] == {"moeda": "USD"}


def test_comparar_transacao_inexistente(client, proxy):
    assert client.get("/transacoes/999/comparar").status_code == 404


def test_comparar_com_proxy_fora_do_ar(client, proxy):
    proxy["respostas"]["2026-08-14"] = RespostaFalsa(200, {"valor": 5.0})
    proxy["respostas"][None] = requests.ConnectionError("recusada")
    transacao_id = client.post("/transacoes", json=TRANSACAO).json["id"]
    assert client.get(f"/transacoes/{transacao_id}/comparar").status_code == 503


def _criar(client, proxy, **campos):
    dados = {**TRANSACAO, **campos}
    proxy["respostas"].setdefault(dados["data"], RespostaFalsa(200, {"valor": 5.0}))
    resposta = client.post("/transacoes", json=dados)
    assert resposta.status_code == 201, resposta.json
    return resposta.json


def test_put_so_descricao_mantem_cotacao_sem_chamar_proxy(client, proxy):
    transacao = _criar(client, proxy)
    chamadas_antes = len(proxy["chamadas"])

    r = client.put(f"/transacoes/{transacao['id']}", json={**TRANSACAO, "descricao": "Hostel", "valor": 200})

    assert r.status_code == 200
    assert r.json["descricao"] == "Hostel"
    assert r.json["cotacao_utilizada"] == 5.0
    assert r.json["valor_convertido_brl"] == 1000.0
    assert len(proxy["chamadas"]) == chamadas_antes


def test_put_nova_data_busca_nova_cotacao(client, proxy):
    transacao = _criar(client, proxy)
    proxy["respostas"]["2026-09-01"] = RespostaFalsa(200, {"valor": 5.5})

    r = client.put(f"/transacoes/{transacao['id']}", json={**TRANSACAO, "data": "2026-09-01"})

    assert r.status_code == 200
    assert r.json["cotacao_utilizada"] == 5.5
    assert r.json["valor_convertido_brl"] == 550.0


def test_put_invalido_e_inexistente(client, proxy):
    transacao = _criar(client, proxy)
    assert client.put(f"/transacoes/{transacao['id']}", json={"valor": -1}).status_code == 400
    assert client.put("/transacoes/999", json=TRANSACAO).status_code == 404


def test_put_com_proxy_fora_nao_altera(client, proxy):
    transacao = _criar(client, proxy)
    proxy["respostas"]["2026-09-01"] = requests.ConnectionError("recusada")

    r = client.put(f"/transacoes/{transacao['id']}", json={**TRANSACAO, "data": "2026-09-01"})

    assert r.status_code == 503
    assert client.get(f"/transacoes/{transacao['id']}").json["data"] == "2026-08-14"


def test_delete(client, proxy):
    transacao = _criar(client, proxy)
    assert client.delete(f"/transacoes/{transacao['id']}").status_code == 200
    assert client.get(f"/transacoes/{transacao['id']}").status_code == 404
    assert client.delete(f"/transacoes/{transacao['id']}").status_code == 404


def test_filtros_e_ordenacao(client, proxy):
    _criar(client, proxy, descricao="Hotel", valor=300, data="2026-08-10")
    _criar(client, proxy, descricao="Jantar", valor=50, data="2026-08-20")
    _criar(client, proxy, descricao="Mercado", valor=80, moeda="BRL", data="2026-09-01")

    descricoes = lambda r: [t["descricao"] for t in r.json]
    assert descricoes(client.get("/transacoes")) == ["Mercado", "Jantar", "Hotel"]
    assert descricoes(client.get("/transacoes?moeda=usd")) == ["Jantar", "Hotel"]
    assert descricoes(client.get("/transacoes?data_inicio=2026-08-15&data_fim=2026-08-31")) == ["Jantar"]
    assert descricoes(client.get("/transacoes?busca=merc")) == ["Mercado"]
    assert descricoes(client.get("/transacoes?ordenar=valor_convertido_brl&ordem=asc")) == [
        "Mercado", "Jantar", "Hotel"
    ]
    assert client.get("/transacoes?ordenar=id;DROP").status_code == 400
    assert client.get("/transacoes?ordem=cima").status_code == 400
    assert client.get("/transacoes?data_inicio=10/08/2026").status_code == 400


def test_resumo(client, proxy):
    _criar(client, proxy, valor=300, data="2026-08-10")
    _criar(client, proxy, valor=50, data="2026-08-20")
    _criar(client, proxy, valor=80, moeda="BRL", data="2026-09-01")

    r = client.get("/transacoes/resumo")

    assert r.status_code == 200
    assert r.json["quantidade"] == 3
    assert r.json["total_brl"] == 1830.0
    assert r.json["por_moeda"] == [
        {"moeda": "USD", "quantidade": 2, "total_original": 350.0, "total_brl": 1750.0},
        {"moeda": "BRL", "quantidade": 1, "total_original": 80.0, "total_brl": 80.0},
    ]
    assert r.json["por_mes"] == [
        {"mes": "2026-08", "quantidade": 2, "total_brl": 1750.0},
        {"mes": "2026-09", "quantidade": 1, "total_brl": 80.0},
    ]
    assert client.get("/transacoes/resumo?moeda=BRL").json["total_brl"] == 80.0


def test_resumo_vazio(client, proxy):
    assert client.get("/transacoes/resumo").json == {
        "quantidade": 0, "total_brl": 0, "por_moeda": [], "por_mes": []
    }


def test_cors_permite_put_e_delete(client, proxy):
    r = client.options("/transacoes/1")
    assert "PUT" in r.headers["Access-Control-Allow-Methods"]
    assert "DELETE" in r.headers["Access-Control-Allow-Methods"]


def test_documentacao(client, proxy):
    assert client.get("/docs").status_code == 200
    especificacao = client.get("/openapi.json").json
    rotas = especificacao["paths"]
    metodos = {m for caminho in rotas.values() for m in caminho if m != "parameters"}
    assert {"get", "post", "put", "delete"} <= metodos
