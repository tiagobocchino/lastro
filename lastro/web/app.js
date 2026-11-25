// Portal do Lastro: login, demandas, grill, execução, auditoria e revisão.
const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const num = (v) => typeof v === "number" ? v.toLocaleString("pt-BR", { maximumFractionDigits: 2 }) : esc(v);
const NOMES = { nova: "nova", grill: "grill", pronta: "pronta para rodar", em_revisao: "aguardando revisor", aprovada: "aprovada", reprovada: "reprovada" };

let sessao = null;
try { sessao = JSON.parse(sessionStorage.getItem("lastro") || "null"); } catch { sessao = null; }
let atual = null;

async function api(caminho, opcoes = {}) {
  const cab = { ...(opcoes.headers || {}) };
  if (sessao) cab.Authorization = `Bearer ${sessao.token}`;
  if (opcoes.json !== undefined) { cab["Content-Type"] = "application/json"; opcoes.body = JSON.stringify(opcoes.json); }
  const r = await fetch(caminho, { ...opcoes, headers: cab });
  if (r.status === 401) { sair(); throw new Error("Sua sessão expirou. Entre de novo."); }
  if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Erro ${r.status}`); }
  return r;
}

function sair() { sessao = null; try { sessionStorage.removeItem("lastro"); } catch {} telaLogin(); }

function logo() { return `<span class="logo"><i><b></b><b></b><b></b></i>lastro</span>`; }

function telaLogin(msg = "") {
  $("#app").innerHTML = `<div class="login"><form class="bloco" id="f-login">
    ${logo()}
    <div><h1>Entrar</h1><p class="quem">Cada empresa tem o seu espaço. Você só vê os dados da sua.</p></div>
    <label for="email">E-mail<input id="email" type="email" required value="ana@demo.lastro" autocomplete="username"></label>
    <label for="senha">Senha<input id="senha" type="password" required value="demo1234" autocomplete="current-password"></label>
    <button class="btn" type="submit">entrar</button>
    <p class="erro-msg" id="msg">${esc(msg)}</p>
    <div class="dica">Contas de teste (senha demo1234):<br>ana@demo.lastro · demandante<br>rui@demo.lastro · revisor de negócio<br>admin@demo.lastro · admin</div>
  </form></div>`;
  $("#f-login").onsubmit = async (e) => {
    e.preventDefault();
    try {
      const r = await api("/api/login", { method: "POST", json: { email: $("#email").value, senha: $("#senha").value } });
      sessao = await r.json();
      try { sessionStorage.setItem("lastro", JSON.stringify(sessao)); } catch {}
      telaPrincipal();
    } catch (err) { $("#msg").textContent = err.message; }
  };
}

async function telaPrincipal() {
  $("#app").innerHTML = `<header>${logo()}<div class="linha-btn" style="align-items:center">
      <span class="quem"><b>${esc(sessao.nome)}</b> · ${esc(sessao.papel)} · ${esc(sessao.tenant)}</span>
      <button class="btn sec" id="sair">sair</button></div></header>
    <div class="grade"><aside><button class="btn" id="nova">nova demanda</button>
      <p class="rot" style="margin:12px 0 0">demandas</p><div id="lista"></div></aside>
    <main id="painel"></main></div>`;
  $("#sair").onclick = sair;
  $("#nova").onclick = () => { atual = null; telaNova(); marcarLista(); };
  await carregarLista();
  if (atual) abrirDemanda(atual); else telaNova();
}

async function carregarLista() {
  const ds = await (await api("/api/demandas")).json();
  $("#lista").innerHTML = ds.length ? ds.map((d) => `<button class="item" data-id="${d.id}"><span>${esc(d.pergunta)}</span><span class="status ${d.status}">${NOMES[d.status] || d.status}</span></button>`).join("")
    : `<p class="quem">Nenhuma demanda ainda. Comece pela primeira pergunta.</p>`;
  document.querySelectorAll(".item").forEach((b) => (b.onclick = () => abrirDemanda(Number(b.dataset.id))));
  marcarLista();
}

function marcarLista() { document.querySelectorAll(".item").forEach((b) => b.classList.toggle("ativo", Number(b.dataset.id) === atual)); }

async function telaNova() {
  const fontes = await (await api("/api/fontes")).json();
  const admin = sessao.papel === "admin";
  $("#painel").innerHTML = `<p class="rot">nova demanda</p><h1>O que você quer saber?</h1>
    <p class="quem">Escreva como perguntaria a um analista. Antes de rodar, o Lastro faz algumas perguntas para não adivinhar regra de negócio.</p>
    <form class="bloco" id="f-nova">
      <label for="pergunta">Pergunta<textarea id="pergunta" required>Quanto cada vendedor vendeu, em valor vendido, nos contratos fechados?</textarea></label>
      <div><p class="rot" style="margin:0 0 8px">fontes (somente leitura)</p><div class="fontes">${fontes.map((f, i) => `<label for="fonte-${f.id}"><input type="checkbox" id="fonte-${f.id}" value="${f.id}" ${i === 0 ? "checked" : ""}>${esc(f.nome)}</label>`).join("") || '<span class="quem">Nenhuma fonte conectada.</span>'}</div></div>
      <div class="linha-btn"><button class="btn" type="submit" id="b-abrir">abrir demanda</button></div>
      <p class="erro-msg" id="msg"></p>
    </form>
    ${admin ? `<h2>Conectar fonte</h2><form class="bloco" id="f-fonte"><label for="arquivo">Arquivo <small>CSV, Parquet, JSON ou Excel. O Lastro só lê; nunca altera a origem.</small><input id="arquivo" type="file" accept=".csv,.parquet,.json,.xlsx" required></label><div class="linha-btn"><button class="btn sec" type="submit">enviar fonte</button></div><p class="erro-msg" id="msg-f"></p></form>` : ""}`;
  $("#f-nova").onsubmit = async (e) => {
    e.preventDefault();
    const ids = [...document.querySelectorAll(".fontes input:checked")].map((i) => Number(i.value));
    if (!ids.length) { $("#msg").textContent = "Escolha pelo menos uma fonte."; return; }
    $("#b-abrir").disabled = true; $("#b-abrir").textContent = "explorador lendo as fontes…";
    try {
      const d = await (await api("/api/demandas", { method: "POST", json: { pergunta: $("#pergunta").value, fontes: ids } })).json();
      atual = d.id; await carregarLista(); abrirDemanda(d.id);
    } catch (err) { $("#msg").textContent = err.message; $("#b-abrir").disabled = false; $("#b-abrir").textContent = "abrir demanda"; }
  };
  if (admin) $("#f-fonte").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(); fd.append("arquivo", $("#arquivo").files[0]);
    try { await api("/api/fontes", { method: "POST", body: fd }); telaNova(); } catch (err) { $("#msg-f").textContent = err.message; }
  };
}

async function abrirDemanda(id) {
  atual = id; marcarLista();
  const d = await (await api(`/api/demandas/${id}`)).json();
  const p = $("#painel");
  let html = `<p class="rot">demanda ${d.id} · <span class="status ${d.status}">${NOMES[d.status] || d.status}</span></p><h1>${esc(d.pergunta)}</h1>`;
  if (d.status === "grill") html += grillHtml(d);
  if (d.status === "pronta") html += `<div class="bloco"><p>Grill respondido. Os agentes vão modelar, construir o pipeline no sandbox, responder e auditar.</p><div class="linha-btn"><button class="btn ouro" id="b-exec">rodar agentes</button></div><p class="erro-msg" id="msg"></p></div>`;
  if (d.resposta) html += resultadoHtml(d);
  if (d.eventos?.length) html += `<h2>Rastro dos agentes</h2><div class="bloco rastro">${d.eventos.map((e) => `<div><b>${esc(e.ator.split("@")[0])}</b><span>${esc(e.acao)} · ${esc(e.detalhe.slice(0, 220))}</span></div>`).join("")}</div>`;
  p.innerHTML = html;
  if ($("#f-grill")) $("#f-grill").onsubmit = (e) => enviarGrill(e, d);
  if ($("#b-exec")) $("#b-exec").onclick = () => executar(d.id);
  document.querySelectorAll("[data-baixar]").forEach((b) => (b.onclick = () => baixar(d.id, b.dataset.baixar)));
  if ($("#f-rev")) $("#f-rev").onsubmit = (e) => revisar(e, d.id);
}

function grillHtml(d) {
  return `<p class="quem">Antes de rodar, responda o que o Lastro não deve adivinhar. Cada resposta sobre a fonte fica gravada e não volta a ser perguntada.</p>
  <form class="bloco" id="f-grill">${d.grill.map((q, i) => `<div class="grill-q"><label for="q-${i}">${esc(q.pergunta)}
    <input type="text" id="q-${i}" data-qid="${esc(q.id)}" value="${esc(q.sugestao)}" list="op-${i}"></label>
    <datalist id="op-${i}">${(q.opcoes || []).map((o) => `<option value="${esc(o)}">`).join("")}</datalist>
    <small class="quem">${q.persistir ? "fica gravada para as próximas demandas" : "vale só para esta demanda"}</small></div>`).join("")}
    <div class="linha-btn"><button class="btn" type="submit" id="b-grill">confirmar respostas</button></div><p class="erro-msg" id="msg"></p></form>`;
}

async function enviarGrill(e, d) {
  e.preventDefault();
  const respostas = {}; document.querySelectorAll("[data-qid]").forEach((i) => (respostas[i.dataset.qid] = i.value));
  try { await api(`/api/demandas/${d.id}/grill`, { method: "POST", json: respostas }); await carregarLista(); abrirDemanda(d.id); }
  catch (err) { $("#msg").textContent = err.message; }
}

async function executar(id) {
  const b = $("#b-exec"); b.disabled = true; b.textContent = "arquiteto, engenheiro, analista e auditor trabalhando…";
  try { await api(`/api/demandas/${id}/executar`, { method: "POST" }); await carregarLista(); abrirDemanda(id); }
  catch (err) { $("#msg").textContent = err.message; b.disabled = false; b.textContent = "rodar agentes"; }
}

function resultadoHtml(d) {
  const r = d.resposta, a = d.auditoria, m = d.modelo;
  const iv = r.colunas.findIndex((c) => c.startsWith("total_"));
  const maior = iv >= 0 ? Math.max(...r.linhas.map((l) => Math.abs(l[iv] || 0)), 0) : 0;
  const tabela = `<div class="tabela"><table><thead><tr>${r.colunas.map((c) => `<th>${esc(c)}</th>`).join("")}${iv >= 0 ? "<th></th>" : ""}</tr></thead><tbody>${r.linhas.map((l) => `<tr>${l.map((v) => `<td class="${typeof v === "number" ? "n" : ""}">${num(v)}</td>`).join("")}${iv >= 0 && maior ? `<td style="width:28%"><div class="barra" style="width:${(100 * Math.abs(l[iv] || 0) / maior).toFixed(1)}%"></div></td>` : ""}</tr>`).join("")}</tbody></table></div>`;
  const checks = a.checagens.map((c) => `<tr><td class="${c.ok ? "ok" : c.nivel}">${c.ok ? "ok" : c.nivel}</td><td>${esc(c.checagem)}</td><td>${esc(c.detalhe)}</td></tr>`).join("");
  const podeRevisar = d.status === "em_revisao" && ["revisor", "admin"].includes(sessao.papel);
  return `${r.total != null ? `<div class="bloco"><p class="rot" style="margin:0">total de ${esc(r.medida)}</p><div class="total">${num(r.total)}</div></div>` : ""}
    <h2>Resposta</h2><div class="bloco">${tabela}</div>
    <h2>Auditoria técnica · camada 1 <span class="${a.aprovado_camada1 ? "ok" : "erro"}" style="font:600 13px var(--f-dado)">${a.aprovado_camada1 ? "aprovada" : "com erro"}</span></h2>
    <div class="bloco tabela"><table class="chk"><tbody>${checks}</tbody></table></div>
    <h2>Camada 2 · revisor de negócio</h2>
    <div class="bloco"><p>Abra o notebook no Google Colab, refaça as contas e compare com a tabela acima.</p>
      <div class="linha-btn"><button class="btn sec" data-baixar="notebook">baixar notebook do Colab</button><button class="btn sec" data-baixar="relatorio">baixar relatório</button><button class="btn sec" data-baixar="pipeline">baixar pipeline.py</button></div>
      ${d.revisao ? `<p><b>${esc(d.revisao.revisor)}</b> ${d.revisao.aprovado ? "aprovou" : "reprovou"}: ${esc(d.revisao.parecer || "(sem parecer)")}</p>` : ""}
      ${podeRevisar ? `<form id="f-rev" style="display:grid;gap:10px"><label for="parecer">Parecer<textarea id="parecer" placeholder="Ex.: números conferem com o notebook; regra de status correta."></textarea></label>
        <div class="linha-btn"><button class="btn ouro" type="submit" value="1">aprovar entrega</button><button class="btn sec" type="submit" value="0">reprovar</button></div><p class="erro-msg" id="msg-r"></p></form>`
        : d.status === "em_revisao" ? `<p class="quem">Aguardando um revisor de negócio. Entre como rui@demo.lastro para revisar.</p>` : ""}</div>
    <h2>Como chegamos aqui</h2><div class="bloco"><p class="quem">medida <code>${esc(m.medida)}</code> · data <code>${esc(m.data)}</code> · chave <code>${esc(m.chave)}</code> · filtro <code>${esc(m.filtro || "nenhum")}</code><br>dimensões: ${esc(m.dimensoes.join(", "))}<br>playbook consultado: <code>${esc(m.playbook)}</code></p><pre>${esc(r.sql)}</pre></div>`;
}

async function revisar(e, id) {
  e.preventDefault();
  const aprovado = e.submitter?.value === "1";
  try { await api(`/api/demandas/${id}/revisao`, { method: "POST", json: { aprovado, parecer: $("#parecer").value } }); await carregarLista(); abrirDemanda(id); }
  catch (err) { $("#msg-r").textContent = err.message; }
}

async function baixar(id, tipo) {
  const r = await api(`/api/demandas/${id}/arquivo/${tipo}`);
  const url = URL.createObjectURL(await r.blob());
  const a = document.createElement("a"); a.href = url; a.download = `demanda${id}_${tipo === "notebook" ? "auditoria_colab.ipynb" : tipo === "pipeline" ? "pipeline.py" : "relatorio.html"}`;
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
}

sessao ? telaPrincipal() : telaLogin();
