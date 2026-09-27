// Cliente do back-end principal. O front nunca fala com o módulo de câmbio
// nem com a API externa: Front → Back → Proxy/Cache → AwesomeAPI.
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

async function requisitar(caminho, opcoes = {}) {
  let resposta;
  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      headers: { "Content-Type": "application/json" },
      ...opcoes,
    });
  } catch {
    throw new Error(
      `Não foi possível conectar ao back-end (${API_URL}). Verifique se ele está rodando.`
    );
  }

  let corpo = null;
  try {
    corpo = await resposta.json();
  } catch {
    // resposta sem JSON
  }

  if (!resposta.ok) {
    throw new Error(corpo?.erro || `Erro ${resposta.status} ao falar com o back-end.`);
  }
  return corpo;
}

// Monta a query string ignorando filtros vazios
function query(filtros = {}) {
  const parametros = new URLSearchParams(
    Object.entries(filtros).filter(([, valor]) => valor !== "" && valor != null)
  ).toString();
  return parametros ? `?${parametros}` : "";
}

export function listarTransacoes(filtros) {
  return requisitar(`/transacoes${query(filtros)}`);
}

export function obterResumo(filtros) {
  const { moeda, data_inicio, data_fim, busca } = filtros || {};
  return requisitar(`/transacoes/resumo${query({ moeda, data_inicio, data_fim, busca })}`);
}

export function criarTransacao(dados) {
  return requisitar("/transacoes", { method: "POST", body: JSON.stringify(dados) });
}

export function atualizarTransacao(id, dados) {
  return requisitar(`/transacoes/${id}`, { method: "PUT", body: JSON.stringify(dados) });
}

export function excluirTransacao(id) {
  return requisitar(`/transacoes/${id}`, { method: "DELETE" });
}

export function compararTransacao(id) {
  return requisitar(`/transacoes/${id}/comparar`);
}
