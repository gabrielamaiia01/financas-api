export function formatarMoeda(valor, moeda = "BRL") {
  if (valor === null || valor === undefined) return "—";
  try {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: moeda }).format(valor);
  } catch {
    // código de moeda que o navegador não conhece
    return `${moeda} ${formatarNumero(valor, 2)}`;
  }
}

export function formatarNumero(valor, casas = 4) {
  if (valor === null || valor === undefined) return "—";
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  }).format(valor);
}

// "2026-08-15" → "15/08/2026" (sem passar por Date, para não sofrer com fuso)
export function formatarData(dataIso) {
  if (!dataIso) return "—";
  const [ano, mes, dia] = dataIso.split("-");
  return `${dia}/${mes}/${ano}`;
}

export function formatarPercentual(valor) {
  if (valor === null || valor === undefined) return "—";
  const sinal = valor > 0 ? "+" : "";
  return `${sinal}${formatarNumero(valor, 2)}%`;
}

// Data de hoje no fuso local, em AAAA-MM-DD (para o max do input de data)
export function hojeIso() {
  const agora = new Date();
  const local = new Date(agora.getTime() - agora.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}
