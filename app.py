from flask import Flask, jsonify, request
import requests

from config import MOEDA_PADRAO
from cache import inicializar_cache, buscar_no_cache, salvar_no_cache
from cliente_awesome_api import buscar_cotacao_historica, buscar_cotacao_atual

app = Flask(__name__)


@app.route("/cotacao", methods=["GET"])
def obter_cotacao():
    """Retorna a cotação de uma moeda contra o BRL.

    Query params:
    - moeda: opcional, padrão USD (ex: ?moeda=EUR)
    - data: opcional, formato AAAA-MM-DD. Se omitida, retorna a cotação
      atual (não cacheada). Se informada, primeiro olha o cache local;
      só chama a API externa se ainda não tiver essa (moeda, data).
    """
    moeda = request.args.get("moeda", MOEDA_PADRAO).upper()
    data = request.args.get("data")

    if data:
        valor_em_cache = buscar_no_cache(moeda, data)
        if valor_em_cache is not None:
            return jsonify(
                {"moeda": moeda, "data": data, "valor": valor_em_cache, "origem": "cache"}
            ), 200

        try:
            resultado = buscar_cotacao_historica(moeda, data)
        except requests.RequestException:
            return jsonify({"erro": "Não foi possível consultar a API externa de câmbio."}), 502

        if resultado is None:
            return jsonify(
                {"erro": f"Não há cotação de {moeda} para {data} (fim de semana ou feriado)."}
            ), 404

        salvar_no_cache(moeda, data, resultado["valor"])
        return jsonify(
            {"moeda": moeda, "data": data, "valor": resultado["valor"], "origem": "api_externa"}
        ), 200

    # Sem data: cotação em tempo real, sempre buscada na API (não cacheada)
    try:
        resultado = buscar_cotacao_atual(moeda)
    except requests.RequestException:
        return jsonify({"erro": "Não foi possível consultar a API externa de câmbio."}), 502

    return jsonify(
        {
            "moeda": moeda,
            "data": resultado["data"],
            "valor": resultado["valor"],
            "origem": "api_externa",
        }
    ), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    inicializar_cache()
    app.run(debug=True, port=5001)
