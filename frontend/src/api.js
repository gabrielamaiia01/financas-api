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

export function listarTransacoes() {
  return requisitar("/transacoes");
}

export function criarTransacao(dados) {
  return requisitar("/transacoes", { method: "POST", body: JSON.stringify(dados) });
}

export function compararTransacao(id) {
  return requisitar(`/transacoes/${id}/comparar`);
}
