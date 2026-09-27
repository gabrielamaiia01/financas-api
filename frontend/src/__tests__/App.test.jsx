import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App.jsx";

const HOTEL = {
  id: 1,
  descricao: "Hotel",
  valor: 100,
  moeda: "USD",
  data: "2026-08-14",
  cotacao_utilizada: 5.0,
  valor_convertido_brl: 500,
};

function resposta(status, corpo) {
  return Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(corpo) });
}

const RESUMO_VAZIO = { quantidade: 0, total_brl: 0, por_moeda: [], por_mes: [] };

// Simula o back-end: `rotas` mapeia "METODO /caminho" para uma função que gera a resposta
function mockBackend(rotas) {
  const chamadas = [];
  rotas = { "GET /transacoes/resumo": () => resposta(200, RESUMO_VAZIO), ...rotas };
  globalThis.fetch = vi.fn((url, opcoes = {}) => {
    const metodo = opcoes.method || "GET";
    const { pathname: caminho, searchParams } = new URL(url);
    chamadas.push({
      metodo,
      caminho,
      query: Object.fromEntries(searchParams),
      corpo: opcoes.body && JSON.parse(opcoes.body),
    });
    const rota = rotas[`${metodo} ${caminho}`];
    if (!rota) throw new Error(`rota não simulada: ${metodo} ${caminho}`);
    return rota(opcoes, Object.fromEntries(searchParams));
  });
  return chamadas;
}

async function preencherFormulario(usuario, { descricao, valor, moeda, data }) {
  const formulario = within(screen.getByRole("heading", { name: "Nova despesa" }).closest("form"));
  await usuario.type(formulario.getByLabelText("Descrição"), descricao);
  await usuario.type(formulario.getByLabelText("Valor"), String(valor));
  await usuario.selectOptions(formulario.getByLabelText("Moeda"), moeda);
  const campoData = formulario.getByLabelText("Data da compra");
  await usuario.clear(campoData);
  await usuario.type(campoData, data);
}

describe("App", () => {
  beforeEach(() => vi.restoreAllMocks());
  afterEach(() => delete globalThis.fetch);

  it("lista as transações com cotação e valor em reais", async () => {
    mockBackend({ "GET /transacoes": () => resposta(200, [HOTEL]) });
    render(<App />);

    const linha = (await screen.findByText("Hotel")).closest("tr");
    expect(within(linha).getByText("14/08/2026")).toBeInTheDocument();
    expect(within(linha).getByText("5,0000")).toBeInTheDocument();
    expect(within(linha).getByText(/R\$\s*500,00/)).toBeInTheDocument();
  });

  it("cadastra uma despesa e recarrega a lista", async () => {
    let lista = [];
    const chamadas = mockBackend({
      "GET /transacoes": () => resposta(200, lista),
      "POST /transacoes": () => {
        lista = [HOTEL];
        return resposta(201, HOTEL);
      },
    });
    const usuario = userEvent.setup();
    render(<App />);
    await screen.findByText("Nenhuma despesa cadastrada ainda.");

    await preencherFormulario(usuario, { descricao: "Hotel", valor: 100, moeda: "USD", data: "2026-08-14" });
    await usuario.click(screen.getByRole("button", { name: "Cadastrar" }));

    expect(await screen.findByText("Hotel", { selector: "td" })).toBeInTheDocument();
    const post = chamadas.find((c) => c.metodo === "POST");
    expect(post.corpo).toEqual({ descricao: "Hotel", valor: 100, moeda: "USD", data: "2026-08-14" });
    expect(screen.getByLabelText("Descrição")).toHaveValue("");
  });

  it("mostra a mensagem de erro do back-end e mantém o formulário preenchido", async () => {
    mockBackend({
      "GET /transacoes": () => resposta(200, []),
      "POST /transacoes": () =>
        resposta(502, { erro: "Não foi possível consultar a API externa de câmbio." }),
    });
    const usuario = userEvent.setup();
    render(<App />);
    await screen.findByText("Nenhuma despesa cadastrada ainda.");

    await preencherFormulario(usuario, { descricao: "Hotel", valor: 100, moeda: "USD", data: "2026-08-14" });
    await usuario.click(screen.getByRole("button", { name: "Cadastrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível consultar a API externa de câmbio."
    );
    expect(screen.getByLabelText("Descrição")).toHaveValue("Hotel");
  });

  it("avisa quando o back-end está fora do ar", async () => {
    globalThis.fetch = vi.fn(() => Promise.reject(new TypeError("Failed to fetch")));
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Não foi possível conectar ao back-end");
  });

  it("compara com a cotação atual e mostra a variação", async () => {
    mockBackend({
      "GET /transacoes": () => resposta(200, [HOTEL]),
      "GET /transacoes/1/comparar": () =>
        resposta(200, {
          transacao_id: 1,
          cotacao_utilizada: 5.0,
          cotacao_atual: 5.5,
          variacao_percentual: 10,
          valor_convertido_brl: 500,
          valor_hoje_brl: 550,
          diferenca_brl: 50,
        }),
    });
    const usuario = userEvent.setup();
    render(<App />);

    const linha = (await screen.findByText("Hotel")).closest("tr");
    await usuario.click(within(linha).getByRole("button", { name: "Comparar com hoje" }));

    expect(await within(linha).findByText("+10,00%")).toHaveClass("alta");
    expect(within(linha).getByText("5,5000")).toBeInTheDocument();
    expect(within(linha).getByText(/R\$\s*550,00/)).toBeInTheDocument();
  });

  it("mostra o erro da comparação na linha", async () => {
    mockBackend({
      "GET /transacoes": () => resposta(200, [HOTEL]),
      "GET /transacoes/1/comparar": () =>
        resposta(503, { erro: "O serviço de câmbio está indisponível no momento." }),
    });
    const usuario = userEvent.setup();
    render(<App />);

    const linha = (await screen.findByText("Hotel")).closest("tr");
    await usuario.click(within(linha).getByRole("button", { name: "Comparar com hoje" }));
    expect(await within(linha).findByText(/serviço de câmbio está indisponível/)).toBeInTheDocument();
  });

  it("edita uma despesa com PUT", async () => {
    let lista = [HOTEL];
    const chamadas = mockBackend({
      "GET /transacoes": () => resposta(200, lista),
      "PUT /transacoes/1": (opcoes) => {
        lista = [{ ...HOTEL, ...JSON.parse(opcoes.body) }];
        return resposta(200, lista[0]);
      },
    });
    const usuario = userEvent.setup();
    render(<App />);

    await usuario.click(await screen.findByRole("button", { name: "Editar Hotel" }));
    expect(screen.getByRole("heading", { name: "Editar despesa #1" })).toBeInTheDocument();
    expect(screen.getByLabelText("Descrição")).toHaveValue("Hotel");

    await usuario.clear(screen.getByLabelText("Descrição"));
    await usuario.type(screen.getByLabelText("Descrição"), "Hostel");
    await usuario.click(screen.getByRole("button", { name: "Salvar alterações" }));

    expect(await screen.findByText("Hostel", { selector: "td" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Nova despesa" })).toBeInTheDocument();
    const put = chamadas.find((c) => c.metodo === "PUT");
    expect(put.corpo).toEqual({ descricao: "Hostel", valor: 100, moeda: "USD", data: "2026-08-14" });
  });

  it("exclui uma despesa com DELETE após confirmação", async () => {
    let lista = [HOTEL];
    const chamadas = mockBackend({
      "GET /transacoes": () => resposta(200, lista),
      "DELETE /transacoes/1": () => {
        lista = [];
        return resposta(200, { mensagem: "Transação 1 excluída." });
      },
    });
    const confirmar = vi.spyOn(window, "confirm");
    const usuario = userEvent.setup();
    render(<App />);

    confirmar.mockReturnValueOnce(false);
    await usuario.click(await screen.findByRole("button", { name: "Excluir Hotel" }));
    expect(chamadas.some((c) => c.metodo === "DELETE")).toBe(false);

    confirmar.mockReturnValueOnce(true);
    await usuario.click(screen.getByRole("button", { name: "Excluir Hotel" }));
    expect(await screen.findByText("Nenhuma despesa cadastrada ainda.")).toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "DELETE" && c.caminho === "/transacoes/1")).toBe(true);
  });

  it("envia os filtros e a ordenação para a API", async () => {
    const chamadas = mockBackend({ "GET /transacoes": () => resposta(200, []) });
    const usuario = userEvent.setup();
    render(<App />);
    await screen.findByText("Nenhuma despesa cadastrada ainda.");

    await usuario.selectOptions(screen.getAllByLabelText("Moeda")[1], "EUR");
    await usuario.selectOptions(screen.getByLabelText("Ordenar"), "valor_convertido_brl:desc");

    expect(await screen.findByText("Nenhuma despesa encontrada com esses filtros.")).toBeInTheDocument();
    const ultima = chamadas.filter((c) => c.caminho === "/transacoes").at(-1);
    expect(ultima.query).toEqual({ moeda: "EUR", ordenar: "valor_convertido_brl", ordem: "desc" });
  });

  it("mostra o gráfico mensal e os totais do resumo", async () => {
    mockBackend({
      "GET /transacoes": () => resposta(200, [HOTEL]),
      "GET /transacoes/resumo": () =>
        resposta(200, {
          quantidade: 1,
          total_brl: 500,
          por_moeda: [{ moeda: "USD", quantidade: 1, total_original: 100, total_brl: 500 }],
          por_mes: [{ mes: "2026-08", quantidade: 1, total_brl: 500 }],
        }),
    });
    render(<App />);

    expect(await screen.findByRole("img", { name: /total gasto em reais por mês/ })).toBeInTheDocument();
    expect(screen.getByText("ago/26", { selector: "td" })).toBeInTheDocument();
    expect(screen.getByText("1 em USD")).toBeInTheDocument();
  });
});
