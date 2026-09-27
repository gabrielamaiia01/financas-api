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
