import { useCallback, useEffect, useState } from "react";
import {
  atualizarTransacao,
  compararTransacao,
  criarTransacao,
  excluirTransacao,
  listarTransacoes,
  obterResumo,
} from "./api.js";
import Filtros, { FILTROS_INICIAIS } from "./components/Filtros.jsx";
import FormularioTransacao from "./components/FormularioTransacao.jsx";
import GraficoMensal from "./components/GraficoMensal.jsx";
import Resumo from "./components/Resumo.jsx";
import TabelaTransacoes from "./components/TabelaTransacoes.jsx";

export default function App() {
  const [transacoes, setTransacoes] = useState([]);
  const [resumo, setResumo] = useState(null);
  const [filtros, setFiltros] = useState(FILTROS_INICIAIS);
  // { [id]: { carregando } | { dados } | { erro } }
  const [comparacoes, setComparacoes] = useState({});
  const [emEdicao, setEmEdicao] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erroLista, setErroLista] = useState("");
  const [aviso, setAviso] = useState("");

  const carregar = useCallback(async () => {
    setErroLista("");
    try {
      const [lista, totais] = await Promise.all([listarTransacoes(filtros), obterResumo(filtros)]);
      setTransacoes(lista);
      setResumo(totais);
    } catch (e) {
      setErroLista(e.message);
    } finally {
      setCarregando(false);
    }
  }, [filtros]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  function esquecerComparacao(id) {
    setComparacoes(({ [id]: _removida, ...resto }) => resto);
  }

  function avisar(mensagem) {
    setAviso(mensagem);
    setTimeout(() => setAviso(""), 3000);
  }

  async function salvar(dados) {
    // Erros sobem para o formulário, que mostra a mensagem do back-end
    if (emEdicao) {
      await atualizarTransacao(emEdicao.id, dados);
      esquecerComparacao(emEdicao.id);
      setEmEdicao(null);
      avisar("Despesa atualizada.");
    } else {
      await criarTransacao(dados);
      avisar("Despesa cadastrada.");
    }
    await carregar();
  }

  async function excluir(transacao) {
    if (!window.confirm(`Excluir "${transacao.descricao}"?`)) return;
    try {
      await excluirTransacao(transacao.id);
      esquecerComparacao(transacao.id);
      if (emEdicao?.id === transacao.id) setEmEdicao(null);
      avisar("Despesa excluída.");
      await carregar();
    } catch (e) {
      setErroLista(e.message);
    }
  }

  async function comparar(id) {
    setComparacoes((atual) => ({ ...atual, [id]: { carregando: true } }));
    try {
      const dados = await compararTransacao(id);
      setComparacoes((atual) => ({ ...atual, [id]: { dados } }));
    } catch (e) {
      setComparacoes((atual) => ({ ...atual, [id]: { erro: e.message } }));
    }
  }

  function compararTodas() {
    transacoes.forEach((t) => comparar(t.id));
  }

  const filtrosAtivos = ["busca", "moeda", "data_inicio", "data_fim"].some((c) => filtros[c]);

  return (
    <div className="pagina">
      <header>
        <h1>Minhas despesas no exterior</h1>
        <p className="discreto">
          Cada despesa é convertida para reais com a cotação do dia da compra.
        </p>
      </header>

      <Resumo resumo={resumo} transacoes={transacoes} comparacoes={comparacoes} />

      <main className="grade">
        <aside className="coluna-lateral">
          <FormularioTransacao
            key={emEdicao?.id ?? "nova"}
            transacao={emEdicao}
            onSalvar={salvar}
            onCancelar={() => setEmEdicao(null)}
          />
          {aviso && (
            <p className="sucesso" role="status">
              {aviso}
            </p>
          )}
        </aside>

        <div className="coluna-principal">
          <GraficoMensal porMes={resumo?.por_mes} />

          {carregando ? (
            <section className="cartao discreto">Carregando...</section>
          ) : erroLista ? (
            <section className="cartao">
              <p className="erro" role="alert">{erroLista}</p>
              <button className="secundario" onClick={carregar}>Tentar novamente</button>
            </section>
          ) : (
            <TabelaTransacoes
              transacoes={transacoes}
              comparacoes={comparacoes}
              filtrosAtivos={filtrosAtivos}
              emEdicao={emEdicao?.id}
              onComparar={comparar}
              onCompararTodas={compararTodas}
              onEditar={setEmEdicao}
              onExcluir={excluir}
            >
              <Filtros filtros={filtros} onAlterar={setFiltros} />
            </TabelaTransacoes>
          )}
        </div>
      </main>
    </div>
  );
}
