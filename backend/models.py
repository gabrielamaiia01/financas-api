import re
import sqlite3
from datetime import date, datetime

from cliente_cambio import CambioError, buscar_cotacao
from config import DATABASE_PATH


class ValidacaoError(Exception):
    """Dados de entrada inválidos (vira HTTP 400)."""


def get_conexao():
    conexao = sqlite3.connect(DATABASE_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco():
    conexao = get_conexao()
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            moeda TEXT NOT NULL,
            data TEXT NOT NULL,
            cotacao_utilizada REAL,
            valor_convertido_brl REAL,
            criado_em TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conexao.commit()
    conexao.close()


def _validar(dados):
    if not isinstance(dados, dict):
        raise ValidacaoError("Envie um JSON com descricao, valor, moeda e data.")

    descricao = str(dados.get("descricao") or "").strip()
    if not descricao:
        raise ValidacaoError("O campo 'descricao' é obrigatório.")

    try:
        valor = float(dados.get("valor"))
    except (TypeError, ValueError):
        raise ValidacaoError("O campo 'valor' deve ser um número.")
    if valor <= 0:
        raise ValidacaoError("O campo 'valor' deve ser maior que zero.")

    moeda = str(dados.get("moeda") or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", moeda):
        raise ValidacaoError("O campo 'moeda' deve ser um código de 3 letras, ex: USD.")

    data = str(dados.get("data") or "").strip()
    try:
        data_transacao = datetime.strptime(data, "%Y-%m-%d").date()
    except ValueError:
        raise ValidacaoError("O campo 'data' deve estar no formato AAAA-MM-DD.")
    if data_transacao > date.today():
        raise ValidacaoError("A data da transação não pode estar no futuro.")

    return descricao, valor, moeda, data


def criar_transacao(dados):
    """Valida os dados, busca a cotação da data da transação no módulo
    de câmbio e salva a transação já com cotacao_utilizada e
    valor_convertido_brl preenchidos.

    Lança ValidacaoError (dados inválidos) ou CambioError (falha na cotação).
    """
    descricao, valor, moeda, data = _validar(dados)

    if moeda == "BRL":
        cotacao = 1.0
    else:
        cotacao = float(buscar_cotacao(moeda, data)["valor"])

    valor_convertido_brl = round(valor * cotacao, 2)

    conexao = get_conexao()
    cursor = conexao.execute(
        """
        INSERT INTO transacoes (descricao, valor, moeda, data, cotacao_utilizada, valor_convertido_brl)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (descricao, valor, moeda, data, cotacao, valor_convertido_brl),
    )
    conexao.commit()
    novo_id = cursor.lastrowid
    conexao.close()
    return buscar_transacao(novo_id)


def listar_transacoes():
    conexao = get_conexao()
    linhas = conexao.execute("SELECT * FROM transacoes ORDER BY data DESC, id DESC").fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


def buscar_transacao(transacao_id):
    conexao = get_conexao()
    linha = conexao.execute("SELECT * FROM transacoes WHERE id = ?", (transacao_id,)).fetchone()
    conexao.close()
    return dict(linha) if linha else None


def comparar_com_cotacao_atual(transacao):
    """Compara a cotação usada na compra com a cotação atual da moeda.

    variacao_percentual > 0 significa que a moeda subiu desde a compra
    (hoje a mesma compra custaria mais em reais).
    """
    moeda = transacao["moeda"]
    cotacao_compra = transacao["cotacao_utilizada"]
    if not cotacao_compra:
        raise CambioError("Esta transação não tem cotação registrada para comparar.", 409)

    if moeda == "BRL":
        cotacao_atual, data_atual = 1.0, date.today().isoformat()
    else:
        resultado = buscar_cotacao(moeda)
        cotacao_atual, data_atual = float(resultado["valor"]), resultado.get("data")

    valor_hoje_brl = round(transacao["valor"] * cotacao_atual, 2)
    return {
        "transacao_id": transacao["id"],
        "moeda": moeda,
        "valor_original": transacao["valor"],
        "data_transacao": transacao["data"],
        "cotacao_utilizada": cotacao_compra,
        "cotacao_atual": cotacao_atual,
        "data_cotacao_atual": data_atual,
        "variacao_percentual": round((cotacao_atual - cotacao_compra) / cotacao_compra * 100, 2),
        "valor_convertido_brl": transacao["valor_convertido_brl"],
        "valor_hoje_brl": valor_hoje_brl,
        "diferenca_brl": round(valor_hoje_brl - transacao["valor_convertido_brl"], 2),
    }
