import { useCallback, useEffect, useState } from "react";
import { compararTransacao, criarTransacao, listarTransacoes } from "./api.js";
import FormularioTransacao from "./components/FormularioTransacao.jsx";
import Resumo from "./components/Resumo.jsx";
import TabelaTransacoes from "./components/TabelaTransacoes.jsx";

export default function App() {
  const [transacoes, setTransacoes] = useState([]);
  // { [id]: { carregando } | { dados } | { erro } }
  const [comparacoes, setComparacoes] = useState({});
  const [carregando, setCarregando] = useState(true);
  const [erroLista, setErroLista] = useState("");

  const carregar = useCallback(async () => {
    setErroLista("");
    try {
      setTransacoes(await listarTransacoes());
    } catch (e) {
      setErroLista(e.message);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  async function cadastrar(dados) {
    // Erros sobem para o formulário, que mostra a mensagem do back-end
    await criarTransacao(dados);
    await carregar();
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

  return (
    <div className="pagina">
      <header>
        <h1>Minhas despesas no exterior</h1>
        <p className="discreto">
          Cada despesa é convertida para reais com a cotação do dia da compra.
        </p>
      </header>

      <Resumo transacoes={transacoes} comparacoes={comparacoes} />

      <main className="grade">
        <FormularioTransacao onCriar={cadastrar} />

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
            onComparar={comparar}
            onCompararTodas={compararTodas}
          />
        )}
      </main>
    </div>
  );
}
