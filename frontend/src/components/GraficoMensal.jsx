import { useState } from "react";
import { formatarMoeda } from "../formatadores.js";

const NOMES_MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

// "2026-08" → "ago/26"
function rotuloMes(mes) {
  const [ano, numero] = mes.split("-");
  return `${NOMES_MESES[Number(numero) - 1]}/${ano.slice(2)}`;
}

// Arredonda o topo do eixo para um valor "redondo" (1, 2, 2,5 ou 5 × 10^n)
function topoEixo(maximo) {
  if (maximo <= 0) return 1;
  const potencia = 10 ** Math.floor(Math.log10(maximo));
  const passo = [1, 2, 2.5, 5, 10].find((m) => m * potencia >= maximo);
  return passo * potencia;
}

const ALTURA = 180;
const MARGEM_ESQUERDA = 64;
const MARGEM_BASE = 24;
const MARGEM_TOPO = 12;

export default function GraficoMensal({ porMes }) {
  const [ativo, setAtivo] = useState(null);

  if (!porMes?.length) return null;

  const topo = topoEixo(Math.max(...porMes.map((m) => m.total_brl)));
  const larguraColuna = 64;
  const largura = MARGEM_ESQUERDA + porMes.length * larguraColuna;
  const larguraBarra = Math.min(32, larguraColuna - 16);
  const alturaUtil = ALTURA - MARGEM_BASE;
  const alturaGrafico = alturaUtil - MARGEM_TOPO;
  const y = (valor) => alturaUtil - (valor / topo) * alturaGrafico;
  const linhasGrade = [0, 0.5, 1].map((f) => f * topo);
  const maiorMes = porMes.reduce((a, b) => (b.total_brl > a.total_brl ? b : a));

  return (
    <section className="cartao grafico">
      <h2>Gastos por mês (em reais)</h2>
      <div className="grafico-area">
        <svg
          viewBox={`0 0 ${largura} ${ALTURA}`}
          width={largura}
          height={ALTURA}
          role="img"
          aria-label="Gráfico de barras com o total gasto em reais por mês"
        >
          {linhasGrade.map((valor) => (
            <g key={valor}>
              <line className="grade-linha" x1={MARGEM_ESQUERDA} x2={largura} y1={y(valor) + 0.5} y2={y(valor) + 0.5} />
              <text className="eixo" x={MARGEM_ESQUERDA - 8} y={y(valor) + 4} textAnchor="end">
                {formatarMoeda(valor).replace(",00", "")}
              </text>
            </g>
          ))}
          {porMes.map((m, i) => {
            const centro = MARGEM_ESQUERDA + i * larguraColuna + larguraColuna / 2;
            const altura = Math.max(alturaUtil - y(m.total_brl), 1);
            const raio = Math.min(4, altura);
            const x = centro - larguraBarra / 2;
            const topoBarra = alturaUtil - altura;
            return (
              <g
                key={m.mes}
                onMouseEnter={() => setAtivo(m)}
                onMouseLeave={() => setAtivo(null)}
                className={ativo && ativo.mes !== m.mes ? "esmaecida" : ""}
              >
                {/* área de toque maior que a barra */}
                <rect x={centro - larguraColuna / 2} y={0} width={larguraColuna} height={alturaUtil} fill="transparent" />
                <path
                  className="barra"
                  d={`M${x},${alturaUtil} V${topoBarra + raio} Q${x},${topoBarra} ${x + raio},${topoBarra}
                      H${x + larguraBarra - raio} Q${x + larguraBarra},${topoBarra} ${x + larguraBarra},${topoBarra + raio}
                      V${alturaUtil} Z`}
                />
                {m.mes === maiorMes.mes && !ativo && (
                  <text className="rotulo-valor" x={centro} y={topoBarra - 6} textAnchor="middle">
                    {formatarMoeda(m.total_brl).replace(/,\d\d$/, "")}
                  </text>
                )}
                <text className="eixo" x={centro} y={ALTURA - 6} textAnchor="middle">
                  {rotuloMes(m.mes)}
                </text>
              </g>
            );
          })}
        </svg>
        {ativo && (
          <div
            className="dica"
            style={{
              left: MARGEM_ESQUERDA + porMes.indexOf(ativo) * larguraColuna + larguraColuna / 2,
            }}
            role="status"
          >
            <strong>{rotuloMes(ativo.mes)}</strong>
            <span>{formatarMoeda(ativo.total_brl)}</span>
            <small>
              {ativo.quantidade} {ativo.quantidade === 1 ? "despesa" : "despesas"}
            </small>
          </div>
        )}
      </div>

      {/* Mesmos dados em tabela, para leitores de tela */}
      <table className="so-leitor-de-tela">
        <caption>Total gasto por mês</caption>
        <thead>
          <tr>
            <th>Mês</th>
            <th>Total em reais</th>
            <th>Despesas</th>
          </tr>
        </thead>
        <tbody>
          {porMes.map((m) => (
            <tr key={m.mes}>
              <td>{rotuloMes(m.mes)}</td>
              <td>{formatarMoeda(m.total_brl)}</td>
              <td>{m.quantidade}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
