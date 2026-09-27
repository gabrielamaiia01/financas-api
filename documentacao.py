"""Especificação OpenAPI da API, servida em /openapi.json e visualizada em /docs."""

_TRANSACAO_ENTRADA = {
    "type": "object",
    "required": ["descricao", "valor", "moeda", "data"],
    "properties": {
        "descricao": {"type": "string", "example": "Hotel em Nova York"},
        "valor": {"type": "number", "example": 320.0},
        "moeda": {"type": "string", "example": "USD", "description": "Código ISO de 3 letras"},
        "data": {"type": "string", "format": "date", "example": "2026-08-14"},
    },
}

_TRANSACAO = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "example": 1},
        **_TRANSACAO_ENTRADA["properties"],
        "cotacao_utilizada": {"type": "number", "example": 5.43},
        "valor_convertido_brl": {"type": "number", "example": 1737.6},
        "criado_em": {"type": "string", "example": "2026-09-27 20:25:53"},
    },
}

_ERRO = {"type": "object", "properties": {"erro": {"type": "string"}}}


def _resposta(descricao, schema=None):
    resposta = {"description": descricao}
    if schema:
        resposta["content"] = {"application/json": {"schema": schema}}
    return resposta


_ERROS_CAMBIO = {
    "400": _resposta("Dados inválidos (inclui data futura e moeda inválida)", {"$ref": "#/components/schemas/Erro"}),
    "404": _resposta("Sem cotação para a data", {"$ref": "#/components/schemas/Erro"}),
    "502": _resposta("API externa de câmbio fora do ar", {"$ref": "#/components/schemas/Erro"}),
    "503": _resposta("Módulo de câmbio fora do ar", {"$ref": "#/components/schemas/Erro"}),
}

_ID = {"name": "transacao_id", "in": "path", "required": True, "schema": {"type": "integer"}}

_FILTROS = [
    {"name": "moeda", "in": "query", "schema": {"type": "string"}, "example": "USD"},
    {"name": "data_inicio", "in": "query", "schema": {"type": "string", "format": "date"}},
    {"name": "data_fim", "in": "query", "schema": {"type": "string", "format": "date"}},
    {"name": "busca", "in": "query", "schema": {"type": "string"}, "description": "Trecho da descrição"},
]

_NAO_ENCONTRADA = _resposta("Transação não encontrada", {"$ref": "#/components/schemas/Erro"})
_REF_TRANSACAO = {"$ref": "#/components/schemas/Transacao"}
_REF_ENTRADA = {
    "required": True,
    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TransacaoEntrada"}}},
}

ESPECIFICACAO = {
    "openapi": "3.0.3",
    "info": {
        "title": "Finanças API",
        "version": "1.0.0",
        "description": "Despesas em moeda estrangeira convertidas para reais pela cotação do dia da compra.",
    },
    "tags": [{"name": "Transações"}],
    "paths": {
        "/transacoes": {
            "get": {
                "tags": ["Transações"],
                "summary": "Lista transações com filtros e ordenação",
                "parameters": _FILTROS + [
                    {"name": "ordenar", "in": "query", "schema": {
                        "type": "string", "default": "data",
                        "enum": ["data", "valor", "valor_convertido_brl", "descricao", "moeda"]}},
                    {"name": "ordem", "in": "query", "schema": {
                        "type": "string", "default": "desc", "enum": ["asc", "desc"]}},
                ],
                "responses": {
                    "200": _resposta("Lista de transações", {"type": "array", "items": _REF_TRANSACAO}),
                    "400": _resposta("Filtro inválido", {"$ref": "#/components/schemas/Erro"}),
                },
            },
            "post": {
                "tags": ["Transações"],
                "summary": "Cria uma transação e converte o valor para reais",
                "requestBody": _REF_ENTRADA,
                "responses": {"201": _resposta("Transação criada", _REF_TRANSACAO), **_ERROS_CAMBIO},
            },
        },
        "/transacoes/resumo": {
            "get": {
                "tags": ["Transações"],
                "summary": "Totais em reais: geral, por moeda e por mês",
                "parameters": _FILTROS,
                "responses": {"200": _resposta("Resumo", {"type": "object", "properties": {
                    "quantidade": {"type": "integer"},
                    "total_brl": {"type": "number"},
                    "por_moeda": {"type": "array", "items": {"type": "object"}},
                    "por_mes": {"type": "array", "items": {"type": "object"}},
                }})},
            }
        },
        "/transacoes/{transacao_id}": {
            "parameters": [_ID],
            "get": {
                "tags": ["Transações"],
                "summary": "Detalha uma transação",
                "responses": {"200": _resposta("Transação", _REF_TRANSACAO), "404": _NAO_ENCONTRADA},
            },
            "put": {
                "tags": ["Transações"],
                "summary": "Atualiza uma transação (busca nova cotação se a moeda ou a data mudarem)",
                "requestBody": _REF_ENTRADA,
                "responses": {"200": _resposta("Transação atualizada", _REF_TRANSACAO),
                              **_ERROS_CAMBIO, "404": _NAO_ENCONTRADA},
            },
            "delete": {
                "tags": ["Transações"],
                "summary": "Exclui uma transação",
                "responses": {"200": _resposta("Transação excluída"), "404": _NAO_ENCONTRADA},
            },
        },
        "/transacoes/{transacao_id}/comparar": {
            "parameters": [_ID],
            "get": {
                "tags": ["Transações"],
                "summary": "Compara a cotação da compra com a cotação atual",
                "responses": {
                    "200": _resposta("Comparação", {"type": "object", "properties": {
                        "cotacao_utilizada": {"type": "number"},
                        "cotacao_atual": {"type": "number"},
                        "variacao_percentual": {"type": "number"},
                        "valor_convertido_brl": {"type": "number"},
                        "valor_hoje_brl": {"type": "number"},
                        "diferenca_brl": {"type": "number"},
                    }}),
                    "404": _NAO_ENCONTRADA,
                    "502": _ERROS_CAMBIO["502"],
                    "503": _ERROS_CAMBIO["503"],
                },
            },
        },
    },
    "components": {
        "schemas": {"TransacaoEntrada": _TRANSACAO_ENTRADA, "Transacao": _TRANSACAO, "Erro": _ERRO}
    },
}

PAGINA_SWAGGER = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Finanças API — documentação</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>SwaggerUIBundle({ url: "/openapi.json", dom_id: "#swagger-ui" });</script>
</body>
</html>
"""
