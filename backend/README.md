# Finanças em Moeda Estrangeira — API principal

API REST em **Python/Flask** que guarda despesas feitas em moeda estrangeira e as converte para
reais **pela cotação do dia da compra**. As cotações vêm do módulo
[financas-cambio](https://github.com/gabrielamaiia01/financas-cambio), que consulta a AwesomeAPI
e mantém um cache.

| Repositório | Papel |
|---|---|
| [financas-frontend](https://github.com/gabrielamaiia01/financas-frontend) | Interface em React (contém o `docker-compose.yml` que sobe tudo) |
| **financas-api** (este) | API principal |
| [financas-cambio](https://github.com/gabrielamaiia01/financas-cambio) | Módulo proxy/cache de câmbio |

## Arquitetura

![Fluxograma da arquitetura](docs/arquitetura.png)

## Rotas

Documentação interativa (Swagger) em **<http://localhost:5000/docs>** com a API rodando.

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/transacoes` | Cria uma transação. Busca a cotação da data e preenche `cotacao_utilizada` e `valor_convertido_brl`. |
| `GET` | `/transacoes` | Lista transações. Filtros: `moeda`, `data_inicio`, `data_fim`, `busca`. Ordenação: `ordenar` (`data`, `valor`, `valor_convertido_brl`, `descricao`, `moeda`) e `ordem` (`asc`/`desc`). |
| `GET` | `/transacoes/resumo` | Totais em reais: geral, por moeda e por mês. Aceita os mesmos filtros. |
| `GET` | `/transacoes/{id}` | Detalha uma transação. |
| `PUT` | `/transacoes/{id}` | Atualiza uma transação. Se a moeda ou a data mudarem, busca nova cotação. |
| `DELETE` | `/transacoes/{id}` | Exclui uma transação. |
| `GET` | `/transacoes/{id}/comparar` | Compara a cotação da compra com a atual: `variacao_percentual`, `valor_hoje_brl`, `diferenca_brl`. |
| `GET` | `/health` | Verificação de saúde. |

Exemplo de corpo para `POST` e `PUT`:

```json
{ "descricao": "Hotel em Nova York", "valor": 320, "moeda": "USD", "data": "2026-08-14" }
```

Resposta:

```json
{
  "id": 1, "descricao": "Hotel em Nova York", "valor": 320.0, "moeda": "USD", "data": "2026-08-14",
  "cotacao_utilizada": 5.43, "valor_convertido_brl": 1737.6, "criado_em": "2026-09-27 20:25:53"
}
```

### Erros

Todas as respostas de erro têm o formato `{"erro": "mensagem"}`.

| Código | Quando |
|---|---|
| `400` | Dados inválidos: campo faltando, valor ≤ 0, data futura, moeda inválida, filtro inválido |
| `404` | Transação não encontrada, ou sem cotação para a data |
| `502` | A AwesomeAPI está fora do ar |
| `503` | O módulo de câmbio está fora do ar |

## Como executar

### Com Docker

```bash
docker build -t financas-api .
docker run -p 5000:5000 -e CAMBIO_SERVICE_URL=http://host.docker.internal:5001 financas-api
```

Para subir a aplicação completa (Interface + API + câmbio) use o `docker-compose.yml` do repositório
[financas-frontend](https://github.com/gabrielamaiia01/financas-frontend).

### Ambiente de desenvolvimento

Pré-requisito: Python 3.10+ e o módulo de câmbio rodando em `http://localhost:5001`.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python app.py                    # http://localhost:5000
```

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `CAMBIO_SERVICE_URL` | `http://localhost:5001` | Endereço do módulo de câmbio |
| `FINANCAS_DATABASE_PATH` | `financas.db` (na pasta do projeto) | Arquivo do banco SQLite |

## Testes

```bash
pytest
```

Os testes simulam o módulo de câmbio e cobrem todas as rotas, filtros, ordenação, resumo e os
casos de erro (data futura, moeda inválida, câmbio fora do ar).

## Estrutura

```
financas-api/
├── app.py              # rotas Flask
├── models.py           # regras de negócio e acesso ao SQLite
├── cliente_cambio.py   # cliente HTTP do módulo de câmbio
├── documentacao.py     # especificação OpenAPI (Swagger)
├── config.py
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── docs/arquitetura.png
└── tests/
```

## API externa: AwesomeAPI

As cotações vêm da [AwesomeAPI — API de Cotações](https://docs.awesomeapi.com.br/api-de-moedas),
um serviço brasileiro **público e gratuito** com cotações de mais de 150 moedas.

| Item | Informação |
|---|---|
| **Site / documentação** | <https://docs.awesomeapi.com.br/api-de-moedas> |
| **Custo** | Gratuita |
| **Licença de uso** | Não há uma licença formal (ex.: MIT) publicada. O uso é livre e gratuito, sujeito aos termos e limites informados em [awesomeapi.com.br](https://awesomeapi.com.br) e no [aviso sobre limites](https://docs.awesomeapi.com.br/aviso-sobre-limites). |
| **Cadastro** | **Não é necessário.** Sem cadastro, as respostas vêm com cache de 1 minuto no lado da AwesomeAPI, o que é suficiente para este projeto. Opcionalmente, o cadastro gratuito gera uma [API Key](https://docs.awesomeapi.com.br/instrucoes-api-key) com 100 mil requisições por mês sem cache. |
| **Quem chama a API** | Apenas o módulo [financas-cambio](https://github.com/gabrielamaiia01/financas-cambio). A Interface e a API principal nunca falam direto com ela, e o usuário nunca é redirecionado para o site externo: os dados são consumidos, tratados e exibidos dentro da aplicação. |

### Rotas utilizadas

| Rota da AwesomeAPI | Uso no projeto |
|---|---|
| `GET https://economia.awesomeapi.com.br/json/daily/{MOEDA}-BRL/{dias}?start_date=AAAAMMDD&end_date=AAAAMMDD` | Cotação **histórica** de fechamento na data da compra (ex.: `/json/daily/USD-BRL/8?start_date=20260807&end_date=20260814`). Buscamos uma janela de 7 dias para usar o último dia útil quando a compra cai em fim de semana ou feriado. |
| `GET https://economia.awesomeapi.com.br/json/last/{MOEDA}-BRL` | Cotação **atual**, usada na comparação "se fosse hoje" (ex.: `/json/last/USD-BRL`). |

Campos usados da resposta: `bid` (valor de compra da moeda em reais), `timestamp` e `create_date`.
Quando a moeda não existe, a AwesomeAPI responde `404` (`CoinNotExists`), que o módulo de câmbio
transforma em uma mensagem clara para o usuário.
