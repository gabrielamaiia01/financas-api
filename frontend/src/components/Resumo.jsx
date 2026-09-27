import { formatarMoeda, formatarPercentual } from "../formatadores.js";

// `resumo` vem de GET /transacoes/resumo; `comparacoes` são as comparações
// com a cotação atual já feitas na tabela.
export default function Resumo({ resumo, transacoes, comparacoes }) {
  const comparadas = transacoes.filter((t) => comparacoes[t.id]?.dados);
  const compraComparadas = comparadas.reduce((soma, t) => soma + t.valor_convertido_brl, 0);
  const hojeComparadas = comparadas.reduce((soma, t) => soma + comparacoes[t.id].dados.valor_hoje_brl, 0);
  const diferenca = hojeComparadas - compraComparadas;
  const variacao = compraComparadas ? (diferenca / compraComparadas) * 100 : null;

  const moedaPrincipal = resumo?.por_moeda?.find((m) => m.moeda !== "BRL");

  return (
    <section className="resumo">
      <div className="cartao indicador">
        <span>Transações</span>
        <strong>{resumo?.quantidade ?? "—"}</strong>
        {resumo?.por_moeda?.length > 0 && (
          <small className="discreto">
            {resumo.por_moeda.map((m) => `${m.quantidade} em ${m.moeda}`).join(" · ")}
          </small>
        )}
      </div>
      <div className="cartao indicador">
        <span>Total gasto (cotação da compra)</span>
        <strong>{resumo ? formatarMoeda(resumo.total_brl) : "—"}</strong>
        {moedaPrincipal && (
          <small className="discreto">
            Maior parte em {moedaPrincipal.moeda}: {formatarMoeda(moedaPrincipal.total_brl)}
          </small>
        )}
      </div>
      <div className="cartao indicador">
        <span>
          Se fosse hoje
          {comparadas.length < transacoes.length && ` (${comparadas.length} de ${transacoes.length})`}
        </span>
        <strong>{comparadas.length ? formatarMoeda(hojeComparadas) : "—"}</strong>
        {variacao !== null ? (
          <small className={diferenca > 0 ? "alta" : diferenca < 0 ? "baixa" : ""}>
            {formatarPercentual(variacao)} ({formatarMoeda(diferenca)})
          </small>
        ) : (
          <small className="discreto">Use “Comparar” na tabela</small>
        )}
      </div>
    </section>
  );
}
