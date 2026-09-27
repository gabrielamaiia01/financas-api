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


def _obter_cotacao(moeda, data):
    if moeda == "BRL":
        return 1.0
    return float(buscar_cotacao(moeda, data)["valor"])


def criar_transacao(dados):
    """Valida os dados, busca a cotação da data da transação no módulo
    de câmbio e salva a transação já com cotacao_utilizada e
    valor_convertido_brl preenchidos.

    Lança ValidacaoError (dados inválidos) ou CambioError (falha na cotação).
    """
    descricao, valor, moeda, data = _validar(dados)
    cotacao = _obter_cotacao(moeda, data)
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


def atualizar_transacao(transacao_id, dados):
    """Substitui todos os campos de uma transação (semântica de PUT).

    Se a moeda ou a data mudarem, busca a cotação de novo; senão mantém a
    cotação já registrada. Retorna a transação atualizada, ou None se o id
    não existir.
    """
    atual = buscar_transacao(transacao_id)
    if atual is None:
        return None

    descricao, valor, moeda, data = _validar(dados)
    if moeda == atual["moeda"] and data == atual["data"]:
        cotacao = atual["cotacao_utilizada"]
    else:
        cotacao = _obter_cotacao(moeda, data)
    valor_convertido_brl = round(valor * cotacao, 2)

    conexao = get_conexao()
    conexao.execute(
        """
        UPDATE transacoes
        SET descricao = ?, valor = ?, moeda = ?, data = ?,
            cotacao_utilizada = ?, valor_convertido_brl = ?
        WHERE id = ?
        """,
        (descricao, valor, moeda, data, cotacao, valor_convertido_brl, transacao_id),
    )
    conexao.commit()
    conexao.close()
    return buscar_transacao(transacao_id)


def excluir_transacao(transacao_id):
    """Remove a transação. Retorna True se ela existia."""
    conexao = get_conexao()
    cursor = conexao.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
    conexao.commit()
    conexao.close()
    return cursor.rowcount > 0


# Campos pelos quais a listagem pode ser ordenada (?ordenar=...)
CAMPOS_ORDENACAO = ("data", "valor", "valor_convertido_brl", "descricao", "moeda")


def _montar_filtros(filtros):
    """Traduz os filtros da query string em cláusula WHERE + parâmetros."""
    condicoes, parametros = [], []

    moeda = (filtros.get("moeda") or "").strip().upper()
    if moeda:
        condicoes.append("moeda = ?")
        parametros.append(moeda)

    for chave, operador in (("data_inicio", ">="), ("data_fim", "<=")):
        valor = (filtros.get(chave) or "").strip()
        if valor:
            try:
                datetime.strptime(valor, "%Y-%m-%d")
            except ValueError:
                raise ValidacaoError(f"O filtro '{chave}' deve estar no formato AAAA-MM-DD.")
            condicoes.append(f"data {operador} ?")
            parametros.append(valor)

    busca = (filtros.get("busca") or "").strip()
    if busca:
        condicoes.append("descricao LIKE ?")
        parametros.append(f"%{busca}%")

    where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    return where, parametros


def listar_transacoes(filtros=None):
    """Lista transações com filtros e ordenação opcionais.

    filtros: moeda, data_inicio, data_fim, busca (trecho da descrição),
    ordenar (um de CAMPOS_ORDENACAO, padrão data) e ordem (asc|desc, padrão desc).
    """
    filtros = filtros or {}
    where, parametros = _montar_filtros(filtros)

    ordenar = filtros.get("ordenar") or "data"
    if ordenar not in CAMPOS_ORDENACAO:
        raise ValidacaoError(
            f"Não é possível ordenar por '{ordenar}'. Use: {', '.join(CAMPOS_ORDENACAO)}."
        )
    ordem = (filtros.get("ordem") or "desc").lower()
    if ordem not in ("asc", "desc"):
        raise ValidacaoError("O parâmetro 'ordem' deve ser 'asc' ou 'desc'.")

    conexao = get_conexao()
    linhas = conexao.execute(
        # ordenar/ordem já foram validados contra listas fixas acima
        f"SELECT * FROM transacoes {where} ORDER BY {ordenar} {ordem}, id {ordem}",
        parametros,
    ).fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


def resumir_transacoes(filtros=None):
    """Totais gerais, por moeda e por mês (AAAA-MM), respeitando os filtros."""
    where, parametros = _montar_filtros(filtros or {})
    conexao = get_conexao()

    geral = conexao.execute(
        f"SELECT COUNT(*) AS quantidade, COALESCE(SUM(valor_convertido_brl), 0) AS total_brl "
        f"FROM transacoes {where}",
        parametros,
    ).fetchone()
    por_moeda = conexao.execute(
        f"""
        SELECT moeda, COUNT(*) AS quantidade, SUM(valor) AS total_original,
               SUM(valor_convertido_brl) AS total_brl
        FROM transacoes {where}
        GROUP BY moeda ORDER BY total_brl DESC
        """,
        parametros,
    ).fetchall()
    por_mes = conexao.execute(
        f"""
        SELECT substr(data, 1, 7) AS mes, COUNT(*) AS quantidade,
               SUM(valor_convertido_brl) AS total_brl
        FROM transacoes {where}
        GROUP BY mes ORDER BY mes
        """,
        parametros,
    ).fetchall()
    conexao.close()

    return {
        "quantidade": geral["quantidade"],
        "total_brl": round(geral["total_brl"], 2),
        "por_moeda": [
            {**dict(linha), "total_original": round(linha["total_original"], 2),
             "total_brl": round(linha["total_brl"], 2)}
            for linha in por_moeda
        ],
        "por_mes": [{**dict(linha), "total_brl": round(linha["total_brl"], 2)} for linha in por_mes],
    }


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
