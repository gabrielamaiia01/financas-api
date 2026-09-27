from flask import Flask, jsonify, request

from cliente_cambio import CambioError
from config import PORTA
from documentacao import ESPECIFICACAO, PAGINA_SWAGGER
from models import (
    ValidacaoError,
    atualizar_transacao,
    buscar_transacao,
    comparar_com_cotacao_atual,
    criar_transacao,
    excluir_transacao,
    inicializar_banco,
    listar_transacoes,
    resumir_transacoes,
)

app = Flask(__name__)
app.json.ensure_ascii = False

inicializar_banco()


@app.after_request
def liberar_cors(resposta):
    # Permite que o front-end (servido em outra origem) chame a API
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return resposta


@app.errorhandler(ValidacaoError)
def tratar_validacao(erro):
    return jsonify({"erro": str(erro)}), 400


@app.errorhandler(CambioError)
def tratar_cambio(erro):
    return jsonify({"erro": erro.mensagem}), erro.status


def _nao_encontrada(transacao_id):
    return jsonify({"erro": f"Transação {transacao_id} não encontrada."}), 404


@app.route("/transacoes", methods=["POST"])
def post_transacao():
    """Cria uma transação.

    Body JSON: {"descricao": "Hotel", "valor": 120.5, "moeda": "USD", "data": "2026-08-15"}
    A cotação da data é buscada no módulo de câmbio e a resposta já vem com
    cotacao_utilizada e valor_convertido_brl preenchidos.
    """
    transacao = criar_transacao(request.get_json(silent=True))
    return jsonify(transacao), 201


@app.route("/transacoes", methods=["GET"])
def get_transacoes():
    """Lista transações.

    Filtros opcionais: moeda, data_inicio, data_fim, busca (trecho da descrição).
    Ordenação: ordenar=data|valor|valor_convertido_brl|descricao|moeda, ordem=asc|desc.
    """
    return jsonify(listar_transacoes(request.args)), 200


@app.route("/transacoes/resumo", methods=["GET"])
def get_resumo():
    """Totais em reais: geral, por moeda e por mês. Aceita os mesmos filtros da listagem."""
    return jsonify(resumir_transacoes(request.args)), 200


@app.route("/transacoes/<int:transacao_id>", methods=["GET"])
def get_transacao(transacao_id):
    transacao = buscar_transacao(transacao_id)
    if transacao is None:
        return _nao_encontrada(transacao_id)
    return jsonify(transacao), 200


@app.route("/transacoes/<int:transacao_id>", methods=["PUT"])
def put_transacao(transacao_id):
    """Atualiza todos os campos de uma transação (mesmo body do POST).

    Se a moeda ou a data mudarem, a cotação é buscada de novo.
    """
    transacao = atualizar_transacao(transacao_id, request.get_json(silent=True))
    if transacao is None:
        return _nao_encontrada(transacao_id)
    return jsonify(transacao), 200


@app.route("/transacoes/<int:transacao_id>", methods=["DELETE"])
def delete_transacao(transacao_id):
    if not excluir_transacao(transacao_id):
        return _nao_encontrada(transacao_id)
    return jsonify({"mensagem": f"Transação {transacao_id} excluída."}), 200


@app.route("/transacoes/<int:transacao_id>/comparar", methods=["GET"])
def comparar_transacao(transacao_id):
    """Compara a cotação usada na compra com a cotação atual da moeda."""
    transacao = buscar_transacao(transacao_id)
    if transacao is None:
        return _nao_encontrada(transacao_id)
    return jsonify(comparar_com_cotacao_atual(transacao)), 200


@app.route("/", methods=["GET"])
@app.route("/docs", methods=["GET"])
def docs():
    """Documentação interativa (Swagger UI)."""
    return PAGINA_SWAGGER


@app.route("/openapi.json", methods=["GET"])
def openapi():
    return jsonify(ESPECIFICACAO)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORTA)
