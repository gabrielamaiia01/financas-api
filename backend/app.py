from flask import Flask, jsonify, request

from cliente_cambio import CambioError
from config import PORTA
from models import (
    ValidacaoError,
    buscar_transacao,
    comparar_com_cotacao_atual,
    criar_transacao,
    inicializar_banco,
    listar_transacoes,
)

app = Flask(__name__)
app.json.ensure_ascii = False

inicializar_banco()


@app.after_request
def liberar_cors(resposta):
    # Permite que o front-end (servido em outra origem) chame a API
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resposta


@app.route("/transacoes", methods=["POST"])
def post_transacao():
    """Cria uma transação.

    Body JSON: {"descricao": "Hotel", "valor": 120.5, "moeda": "USD", "data": "2026-08-15"}
    A cotação da data é buscada no módulo de câmbio e a resposta já vem com
    cotacao_utilizada e valor_convertido_brl preenchidos.
    """
    try:
        transacao = criar_transacao(request.get_json(silent=True))
    except ValidacaoError as erro:
        return jsonify({"erro": str(erro)}), 400
    except CambioError as erro:
        return jsonify({"erro": erro.mensagem}), erro.status
    return jsonify(transacao), 201


@app.route("/transacoes", methods=["GET"])
def get_transacoes():
    return jsonify(listar_transacoes()), 200


@app.route("/transacoes/<int:transacao_id>", methods=["GET"])
def get_transacao(transacao_id):
    transacao = buscar_transacao(transacao_id)
    if transacao is None:
        return jsonify({"erro": f"Transação {transacao_id} não encontrada."}), 404
    return jsonify(transacao), 200


@app.route("/transacoes/<int:transacao_id>/comparar", methods=["GET"])
def comparar_transacao(transacao_id):
    """Compara a cotação usada na compra com a cotação atual da moeda."""
    transacao = buscar_transacao(transacao_id)
    if transacao is None:
        return jsonify({"erro": f"Transação {transacao_id} não encontrada."}), 404

    try:
        comparacao = comparar_com_cotacao_atual(transacao)
    except CambioError as erro:
        return jsonify({"erro": erro.mensagem}), erro.status
    return jsonify(comparacao), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=PORTA)
