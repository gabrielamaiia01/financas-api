import {
  formatarData,
  formatarMoeda,
  formatarNumero,
  formatarPercentual,
} from "../formatadores.js";

function CelulaComparacao({ comparacao, onComparar }) {
  if (!comparacao || comparacao.erro)
    return (
      <td colSpan={3} className="celula-comparar">
        {comparacao?.erro && (
          <span className="erro-celula" title={comparacao.erro}>
            {comparacao.erro}{" "}
          </span>
        )}
        <button className="link" onClick={onComparar}>
          {comparacao?.erro ? "Tentar de novo" : "Comparar com hoje"}
        </button>
      </td>
    );
  if (comparacao.carregando) return <td colSpan={3} className="discreto">Consultando...</td>;

  const { cotacao_atual, variacao_percentual, valor_hoje_brl } = comparacao.dados;
  const classe = variacao_percentual > 0 ? "alta" : variacao_percentual < 0 ? "baixa" : "";
  return (
    <>
      <td className="numero">{formatarNumero(cotacao_atual)}</td>
      <td className="numero">{formatarMoeda(valor_hoje_brl)}</td>
      <td className={`numero ${classe}`}>{formatarPercentual(variacao_percentual)}</td>
    </>
  );
}

export default function TabelaTransacoes({
  transacoes,
  comparacoes,
  filtrosAtivos,
  emEdicao,
  onComparar,
  onCompararTodas,
  onEditar,
  onExcluir,
  children,
}) {
  const algumaCarregando = Object.values(comparacoes).some((c) => c?.carregando);

  return (
    <section className="cartao">
      <div className="cabecalho-tabela">
        <h2>Transações</h2>
        {transacoes.length > 0 && (
          <button className="secundario" onClick={onCompararTodas} disabled={algumaCarregando}>
            Comparar todas com a cotação atual
          </button>
        )}
      </div>

      {children}

      {transacoes.length === 0 ? (
        <p className="discreto">
          {filtrosAtivos ? "Nenhuma despesa encontrada com esses filtros." : "Nenhuma despesa cadastrada ainda."}
        </p>
      ) : (
        <div className="rolagem">
          <table>
            <thead>
              <tr>
                <th>Data</th>
                <th>Descrição</th>
                <th className="numero">Valor</th>
                <th className="numero">Cotação na compra</th>
                <th className="numero">Em reais</th>
                <th className="numero">Cotação atual</th>
                <th className="numero">Em reais hoje</th>
                <th className="numero">Variação</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {transacoes.map((t) => (
                <tr key={t.id} className={emEdicao === t.id ? "em-edicao" : ""}>
                  <td>{formatarData(t.data)}</td>
                  <td>{t.descricao}</td>
                  <td className="numero">{formatarMoeda(t.valor, t.moeda)}</td>
                  <td className="numero">{formatarNumero(t.cotacao_utilizada)}</td>
                  <td className="numero">{formatarMoeda(t.valor_convertido_brl)}</td>
                  <CelulaComparacao comparacao={comparacoes[t.id]} onComparar={() => onComparar(t.id)} />
                  <td className="acoes-linha">
                    <button className="link" onClick={() => onEditar(t)} aria-label={`Editar ${t.descricao}`}>
                      Editar
                    </button>
                    <button
                      className="link perigo"
                      onClick={() => onExcluir(t)}
                      aria-label={`Excluir ${t.descricao}`}
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
