import { formatarMoeda, formatarPercentual } from "../formatadores.js";

export default function Resumo({ transacoes, comparacoes }) {
  const totalNaCompra = transacoes.reduce((soma, t) => soma + (t.valor_convertido_brl || 0), 0);

  // Só dá para calcular o "hoje" das transações já comparadas
  const comparadas = transacoes.filter((t) => comparacoes[t.id]?.dados);
  const compraComparadas = comparadas.reduce((soma, t) => soma + t.valor_convertido_brl, 0);
  const hojeComparadas = comparadas.reduce((soma, t) => soma + comparacoes[t.id].dados.valor_hoje_brl, 0);
  const diferenca = hojeComparadas - compraComparadas;
  const variacao = compraComparadas ? (diferenca / compraComparadas) * 100 : null;

  return (
    <section className="resumo">
      <div className="cartao indicador">
        <span>Transações</span>
        <strong>{transacoes.length}</strong>
      </div>
      <div className="cartao indicador">
        <span>Total gasto (cotação da compra)</span>
        <strong>{formatarMoeda(totalNaCompra)}</strong>
      </div>
      <div className="cartao indicador">
        <span>
          Se fosse hoje
          {comparadas.length < transacoes.length && ` (${comparadas.length} de ${transacoes.length})`}
        </span>
        <strong>{comparadas.length ? formatarMoeda(hojeComparadas) : "—"}</strong>
        {variacao !== null && (
          <small className={diferenca > 0 ? "alta" : diferenca < 0 ? "baixa" : ""}>
            {formatarPercentual(variacao)} ({formatarMoeda(diferenca)})
          </small>
        )}
      </div>
    </section>
  );
}
