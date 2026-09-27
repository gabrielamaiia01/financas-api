import { useState } from "react";
import { hojeIso } from "../formatadores.js";

const MOEDAS = [
  ["USD", "Dólar americano"],
  ["EUR", "Euro"],
  ["GBP", "Libra esterlina"],
  ["ARS", "Peso argentino"],
  ["CAD", "Dólar canadense"],
  ["JPY", "Iene japonês"],
  ["CHF", "Franco suíço"],
  ["BRL", "Real"],
];

const VAZIO = { descricao: "", valor: "", moeda: "USD", data: "" };

export default function FormularioTransacao({ onCriar }) {
  const [campos, setCampos] = useState(VAZIO);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  function alterar(evento) {
    const { name, value } = evento.target;
    setCampos((atual) => ({ ...atual, [name]: value }));
  }

  async function enviar(evento) {
    evento.preventDefault();
    setErro("");
    setEnviando(true);
    try {
      await onCriar({ ...campos, valor: Number(campos.valor) });
      setCampos(VAZIO);
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="cartao formulario" onSubmit={enviar}>
      <h2>Nova despesa</h2>

      <label>
        Descrição
        <input
          name="descricao"
          value={campos.descricao}
          onChange={alterar}
          placeholder="Ex: Hotel em Lisboa"
          required
        />
      </label>

      <div className="linha">
        <label>
          Valor
          <input
            name="valor"
            type="number"
            min="0.01"
            step="0.01"
            value={campos.valor}
            onChange={alterar}
            placeholder="0,00"
            required
          />
        </label>

        <label>
          Moeda
          <select name="moeda" value={campos.moeda} onChange={alterar}>
            {MOEDAS.map(([codigo, nome]) => (
              <option key={codigo} value={codigo}>
                {codigo} — {nome}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label>
        Data da compra
        <input
          name="data"
          type="date"
          max={hojeIso()}
          value={campos.data}
          onChange={alterar}
          required
        />
      </label>

      {erro && (
        <p className="erro" role="alert">
          {erro}
        </p>
      )}

      <button type="submit" disabled={enviando}>
        {enviando ? "Buscando cotação..." : "Cadastrar"}
      </button>
    </form>
  );
}
