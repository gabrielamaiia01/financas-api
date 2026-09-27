import sqlite3
from config import DATABASE_PATH


def get_conexao():
    conexao = sqlite3.connect(DATABASE_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_cache():
    """Cria a tabela de cache caso não exista.

    Cada linha guarda a cotação de fechamento de uma moeda em uma data
    específica, para não repetir a chamada à API externa quando a mesma
    data for consultada de novo (ex: outra transação na mesma data).
    """
    conexao = get_conexao()
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS cotacoes_cache (
            moeda TEXT NOT NULL,
            data TEXT NOT NULL,
            valor REAL NOT NULL,
            obtido_em TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (moeda, data)
        )
        """
    )
    conexao.commit()
    conexao.close()


def buscar_no_cache(moeda, data):
    """Retorna o valor em cache para (moeda, data), ou None se não existir."""
    conexao = get_conexao()
    linha = conexao.execute(
        "SELECT valor FROM cotacoes_cache WHERE moeda = ? AND data = ?",
        (moeda, data),
    ).fetchone()
    conexao.close()
    return linha["valor"] if linha else None


def salvar_no_cache(moeda, data, valor):
    """Grava (ou substitui) a cotação de uma moeda em uma data no cache."""
    conexao = get_conexao()
    conexao.execute(
        """
        INSERT INTO cotacoes_cache (moeda, data, valor)
        VALUES (?, ?, ?)
        ON CONFLICT(moeda, data) DO UPDATE SET valor = excluded.valor
        """,
        (moeda, data, valor),
    )
    conexao.commit()
    conexao.close()
