import { MOEDAS } from "../moedas.js";

export const FILTROS_INICIAIS = {
  busca: "",
  moeda: "",
  data_inicio: "",
  data_fim: "",
  ordenar: "data",
  ordem: "desc",
};

const ORDENACOES = [
  ["data:desc", "Mais recentes"],
  ["data:asc", "Mais antigas"],
  ["valor_convertido_brl:desc", "Maior valor em reais"],
  ["valor_convertido_brl:asc", "Menor valor em reais"],
  ["descricao:asc", "Descrição (A–Z)"],
];

export default function Filtros({ filtros, onAlterar }) {
  function alterar(evento) {
    const { name, value } = evento.target;
    if (name === "ordenacao") {
      const [ordenar, ordem] = value.split(":");
      onAlterar({ ...filtros, ordenar, ordem });
    } else {
      onAlterar({ ...filtros, [name]: value });
    }
  }

  const ativos = ["busca", "moeda", "data_inicio", "data_fim"].some((c) => filtros[c]);

  return (
    <div className="filtros" role="search">
      <label>
        Buscar
        <input name="busca" value={filtros.busca} onChange={alterar} placeholder="Descrição" />
      </label>
      <label>
        Moeda
        <select name="moeda" value={filtros.moeda} onChange={alterar}>
          <option value="">Todas</option>
          {MOEDAS.map(([codigo]) => (
            <option key={codigo} value={codigo}>
              {codigo}
            </option>
          ))}
        </select>
      </label>
      <label>
        De
        <input name="data_inicio" type="date" value={filtros.data_inicio} onChange={alterar} />
      </label>
      <label>
        Até
        <input name="data_fim" type="date" value={filtros.data_fim} onChange={alterar} />
      </label>
      <label>
        Ordenar
        <select name="ordenacao" value={`${filtros.ordenar}:${filtros.ordem}`} onChange={alterar}>
          {ORDENACOES.map(([valor, rotulo]) => (
            <option key={valor} value={valor}>
              {rotulo}
            </option>
          ))}
        </select>
      </label>
      {ativos && (
        <button
          type="button"
          className="link limpar"
          onClick={() => onAlterar({ ...FILTROS_INICIAIS, ordenar: filtros.ordenar, ordem: filtros.ordem })}
        >
          Limpar filtros
        </button>
      )}
    </div>
  );
}
