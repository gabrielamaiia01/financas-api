# financas-api

Controle de gastos com conversão de moeda estrangeira para BRL na data da compra.

```
Front-end  →  backend/ (porta 5000)  →  cambio/ (porta 5001, proxy/cache)  →  AwesomeAPI
```

## Módulos

### `cambio/` — proxy/cache de câmbio

Serviço Flask que consulta a [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas)
e guarda as cotações históricas em cache SQLite (`cache_cambio.db`), para não
repetir a chamada externa para a mesma moeda e data.

| Rota | Descrição |
|---|---|
| `GET /cotacao?data=2026-08-14&moeda=USD` | Cotação de fechamento da data. Fim de semana/feriado usa o último dia útil anterior (campo `data_cotacao`). |
| `GET /cotacao?moeda=USD` | Cotação atual (não cacheada). |
| `GET /health` | Verificação de saúde. |

Erros: `400` moeda/data inválida ou data futura · `404` sem cotação · `502` API externa fora do ar.

### `backend/` — API principal

| Rota | Descrição |
|---|---|
| `POST /transacoes` | Cria uma transação. Body: `{"descricao": "Hotel", "valor": 100, "moeda": "USD", "data": "2026-08-14"}`. Busca a cotação no módulo de câmbio e salva `cotacao_utilizada` e `valor_convertido_brl`. |
| `GET /transacoes` | Lista as transações. |
| `GET /transacoes/<id>` | Detalha uma transação. |
| `GET /transacoes/<id>/comparar` | Compara a cotação usada na compra com a cotação atual (`variacao_percentual`, `valor_hoje_brl`, `diferenca_brl`). |

Erros: `400` dados inválidos (inclui data futura e moeda inválida) · `404` sem cotação ou
transação inexistente · `502` API externa fora do ar · `503` módulo de câmbio fora do ar.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# terminal 1
cd cambio && python app.py       # http://localhost:5001

# terminal 2
cd backend && python app.py      # http://localhost:5000
```

O back-end encontra o módulo de câmbio pela variável `CAMBIO_SERVICE_URL`
(padrão `http://localhost:5001`).

Exemplo:

```bash
curl -X POST localhost:5000/transacoes -H "Content-Type: application/json" \
  -d '{"descricao": "Hotel", "valor": 100, "moeda": "USD", "data": "2026-08-14"}'
curl localhost:5000/transacoes/1/comparar
```

## Testes

```bash
cd cambio && python -m pytest
cd backend && python -m pytest
```
