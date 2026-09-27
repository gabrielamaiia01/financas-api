import { useState } from "react";
import { hojeIso } from "../formatadores.js";
import { MOEDAS } from "../moedas.js";

const VAZIO = { descricao: "", valor: "", moeda: "USD", data: "" };

function camposIniciais(transacao) {
  if (!transacao) return VAZIO;
  const { descricao, valor, moeda, data } = transacao;
  return { descricao, valor: String(valor), moeda, data };
}

// Serve para criar (sem `transacao`) e para editar (com `transacao`).
// Quem usa deve passar key={transacao?.id} para reiniciar os campos ao trocar.
export default function FormularioTransacao({ transacao, onSalvar, onCancelar }) {
  const editando = Boolean(transacao);
  const [campos, setCampos] = useState(() => camposIniciais(transacao));
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
      await onSalvar({ ...campos, valor: Number(campos.valor) });
      if (!editando) setCampos(VAZIO);
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className={`cartao formulario ${editando ? "editando" : ""}`} onSubmit={enviar}>
      <h2>{editando ? `Editar despesa #${transacao.id}` : "Nova despesa"}</h2>

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

      <div className="acoes">
        <button type="submit" disabled={enviando}>
          {enviando ? "Buscando cotação..." : editando ? "Salvar alterações" : "Cadastrar"}
        </button>
        {editando && (
          <button type="button" className="secundario" onClick={onCancelar} disabled={enviando}>
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}
