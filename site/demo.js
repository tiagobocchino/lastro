// Teste com a sua planilha (LST-43): planilha → perguntas → painel conferido → recibo do apagamento.
// Fala com /api/demo (LST-39 a LST-42). Nada do visitante fica guardado no navegador além da tela.
(() => {
  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const palco = $("#palco");
  if (!palco) return;
  const inicial = palco.innerHTML;
  const WHATS = "5561999520802";
  const PAPEL = { numero: "valor", data: "data", texto: "categoria", pessoal: "dado pessoal, fora do painel" };
  let sessao = null;
  let ultimo = null;
  let formatoChave = null;
  const plural = (n, um, varios) => `${n.toLocaleString("pt-BR")} ${n === 1 ? um : varios}`;
  const suave = () => (matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth");

  async function chamar(caminho, opcoes = {}) {
    const r = await fetch(caminho, opcoes);
    let corpo = {};
    try { corpo = await r.json(); } catch { corpo = {}; }
    if (!r.ok) {
      const e = new Error(corpo.detail || "Não deu certo agora. Tente de novo em instantes.");
      e.status = r.status;
      e.espera = Number(r.headers.get("retry-after") || 0);
      throw e;
    }
    return corpo;
  }

  // Fila cheia (503): espera o que o servidor pediu e tenta de novo, mostrando a contagem.
  async function comFila(fazer, aviso) {
    for (let tentativa = 0; tentativa < 6; tentativa++) {
      try { return await fazer(); }
      catch (e) {
        if (e.status !== 503) throw e;
        for (let s = e.espera || 10; s > 0; s--) {
          aviso(`Tem gente analisando agora e você é o próximo. Tentando de novo em ${s} s…`);
          await new Promise((ok) => setTimeout(ok, 1000));
        }
      }
    }
    throw new Error("A fila está longa agora. Tente de novo daqui a pouco.");
  }

  function ligarEnvio() {
    const erro = $("#t-erro");
    const enviar = async (exemplo) => {
      erro.textContent = "";
      if (!$("#t-aceite").checked) { erro.textContent = "Marque a caixa de aceite para continuar."; $("#t-aceite").focus(); return; }
      const arq = $("#t-arquivo").files[0];
      if (!exemplo && !arq) { erro.textContent = "Escolha uma planilha ou use a de exemplo."; return; }
      if (arq && !exemplo && arq.size > 5 * 1024 * 1024) { erro.textContent = "A planilha passa de 5 MB. Para arquivos maiores, fale com a gente."; return; }
      const botao = $("#t-analisar");
      botao.disabled = true; botao.textContent = "lendo a planilha…";
      try {
        const corpo = new FormData();
        if (exemplo) corpo.append("exemplo", "true"); else corpo.append("arquivo", arq);
        const r = await comFila(() => chamar("/api/demo/sessoes", { method: "POST", body: corpo }), (t) => { erro.textContent = t; });
        sessao = r.sessao;
        mostrarPerguntas(r);
      } catch (e) {
        erro.textContent = e.message;
        botao.disabled = false; botao.textContent = "analisar planilha";
      }
    };
    $("#t-envio").onsubmit = (ev) => { ev.preventDefault(); enviar(false); };
    $("#t-exemplo").onclick = () => enviar(true);
    const nome = () => { const f = $("#t-arquivo").files[0]; $("#t-nome").textContent = f ? f.name : "nenhum arquivo escolhido"; };
    $("#t-arquivo").onchange = nome;
    const zona = $("#t-envio");
    zona.ondragover = (ev) => { ev.preventDefault(); zona.classList.add("sobre"); };
    zona.ondragleave = () => zona.classList.remove("sobre");
    zona.ondrop = (ev) => { ev.preventDefault(); zona.classList.remove("sobre"); if (ev.dataTransfer.files[0]) { $("#t-arquivo").files = ev.dataTransfer.files; nome(); } };
  }

  function mostrarPerguntas(r) {
    const p = r.perfil;
    palco.innerHTML = `
      <h3>2. O que o Lastro entendeu</h3>
      <p><b>${plural(p.linhas, "linha", "linhas")}</b> e <b>${plural(p.colunas.length, "coluna", "colunas")}</b>:</p>
      <div class="chips">${p.colunas.map((c) => `<span class="chip">${esc(c.nome)} · <b>${esc(PAPEL[c.papel] || c.papel)}</b></span>`).join("")}</div>
      ${(r.avisos || []).map((a) => `<p class="nota"><span><b>Dado pessoal.</b> ${esc(a)}</span></p>`).join("")}
      <form id="t-perguntas" style="display:grid;gap:14px">
        <div class="duas">${r.perguntas.map((q) => `<label class="perg" for="q-${esc(q.id)}">${esc(q.pergunta)}
          <select id="q-${esc(q.id)}" data-q="${esc(q.id)}">${q.opcoes.map((o) => `<option ${o === q.sugestao ? "selected" : ""}>${esc(o)}</option>`).join("")}</select></label>`).join("")}</div>
        <p class="miuda">Já deixamos uma sugestão em cada pergunta. Mude o que quiser.</p>
        <div class="acoes"><button class="cta ouro" type="submit" id="t-montar">montar painel</button><button class="cta leve" type="button" id="t-desistir">desistir e apagar</button></div>
        <p class="alerta" id="t-erro" role="alert"></p>
      </form>`;
    $("#t-perguntas").onsubmit = async (ev) => {
      ev.preventDefault();
      const respostas = Object.fromEntries([...document.querySelectorAll("[data-q]")].map((s) => [s.dataset.q, s.value]));
      ultimo = respostas["demo:formato"] || "painel";
      formatoChave = { "ranking (barras)": "ranking", "tabela": "tabela", "evolução no tempo": "evolucao", "só o número": "numero" }[ultimo] || null;
      const botao = $("#t-montar");
      botao.disabled = true; botao.textContent = "montando e conferindo…";
      try {
        const r2 = await comFila(() => chamar(`/api/demo/sessoes/${sessao}/painel`, {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ respostas }),
        }), (t) => { $("#t-erro").textContent = t; });
        sessao = null;
        mostrarPainel(r2);
      } catch (e) {
        $("#t-erro").textContent = e.message;
        botao.disabled = false; botao.textContent = "montar painel";
        if (e.status === 404 || e.status === 504) recomecarDepois(e.message);
      }
    };
    $("#t-desistir").onclick = async () => {
      try { const r3 = await chamar(`/api/demo/sessoes/${sessao}`, { method: "DELETE" }); sessao = null; mostrarRecibo(r3.recibo, null); }
      catch (e) { recomecarDepois(e.message); }
    };
  }

  function bytes(n) {
    return n < 1024 * 1024 ? `${(n / 1024).toLocaleString("pt-BR", { maximumFractionDigits: 0 })} KB`
      : `${(n / 1024 / 1024).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} MB`;
  }

  function reciboHtml(rc) {
    const hora = new Date(rc.apagado_em).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", timeZone: "America/Sao_Paulo" }) + " (Brasília)";
    return `<div class="recibo"><b>${rc.conferido ? "Apagamos tudo" : "Apagamento pendente"} às ${esc(hora)}</b>
      <span>${rc.arquivos} arquivos · ${rc.tabelas} tabelas · ${bytes(rc.bytes)} · ${rc.conferido ? "conferido: a pasta da análise não existe mais" : "a varredura apaga em até 15 min"}</span></div>`;
  }

  function mostrarPainel(r) {
    const msg = encodeURIComponent(`Testei o painel (${ultimo}) no site do Lastro e quero ver com os meus sistemas.`);
    palco.innerHTML = `
      <h3>3. O seu painel</h3>
      ${r.erro ? `<p class="alerta">${esc(r.erro)}</p>` : `
      <span class="selo">demonstração · conferência automática ${r.auditoria.aprovada ? "aprovada" : "com alertas"} · sem revisão humana</span>
      <iframe class="painel-ifr" id="t-ifr" title="Painel gerado com a sua planilha" sandbox></iframe>
      <div class="acoes"><button class="cta" type="button" id="t-baixar">baixar o painel (HTML)</button></div>`}
      ${reciboHtml(r.recibo)}
      <div class="convite">
        <p><b>Isso foi uma planilha, uma vez.</b> No Lastro contratado, o painel liga direto nos seus sistemas (Sienge, Omie, Bling…), passa pela revisão de alguém do seu time e abre no seu Power BI ou Looker Studio.</p>
        <div class="acoes"><a class="cta ouro" href="https://wa.me/${WHATS}?text=${msg}" target="_blank" rel="noopener">conversar no WhatsApp</a><button class="cta leve" type="button" id="t-outra">testar outra planilha</button></div>
      </div>`;
    if (!r.erro) {
      $("#t-ifr").srcdoc = r.html;
      $("#t-baixar").onclick = () => {
        const url = URL.createObjectURL(new Blob([r.html], { type: "text/html" }));
        const a = document.createElement("a"); a.href = url; a.download = "painel-lastro.html"; document.body.append(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 5000);
      };
    }
    $("#t-outra").onclick = recomecar;
    // Funil anônimo (LST-44): só o formato do painel, nunca os dados
    const whats = palco.querySelector('a[href^="https://wa.me/"]');
    if (whats) whats.addEventListener("click", () => { try { navigator.sendBeacon?.("/api/demo/contato", new Blob([JSON.stringify({ visual: formatoChave })], { type: "application/json" })); } catch { /* o clique segue */ } });
    palco.scrollIntoView({ behavior: suave(), block: "start" });
  }

  function mostrarRecibo(rc) {
    palco.innerHTML = `<h3>Análise cancelada</h3>${reciboHtml(rc)}<div class="acoes"><button class="cta leve" type="button" id="t-outra">testar outra planilha</button></div>`;
    $("#t-outra").onclick = recomecar;
  }

  function recomecarDepois(texto) {
    palco.innerHTML = `<p class="alerta">${esc(texto)}</p><div class="acoes"><button class="cta leve" type="button" id="t-outra">começar de novo</button></div>`;
    $("#t-outra").onclick = recomecar;
  }

  function recomecar() { sessao = null; palco.innerHTML = inicial; ligarEnvio(); }

  // Saiu da página no meio: pede para apagar já (a varredura apagaria em até 15 min de qualquer jeito).
  window.addEventListener("pagehide", () => { if (sessao) navigator.sendBeacon?.(`/api/demo/sessoes/${sessao}/apagar`); });

  ligarEnvio();
})();
