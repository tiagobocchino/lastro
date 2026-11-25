// Portal do Lastro: login, demandas, grill, execução, auditoria e revisão.
const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const NOMES_ARQUIVO = { notebook: "auditoria_colab.ipynb", pipeline: "pipeline.py", relatorio: "relatorio.html",
  bigquery: "pipeline_bigquery.sql", azure: "pipeline_azure_sql.sql", athena: "pipeline_athena.sql" };
const plural = (n, um, varios) => `${n} ${n === 1 ? um : varios}`;
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

function guardar() { try { sessionStorage.setItem("lastro", JSON.stringify(sessao)); } catch {} }

function sair() { sessao = null; try { sessionStorage.removeItem("lastro"); } catch {} telaLogin(); }

function logo() { return `<span class="logo"><svg width="22" height="22" viewBox="0 0 64 64" fill="none" aria-hidden="true"><rect x="8" y="8" width="32" height="32" rx="3" stroke="var(--tinta)" stroke-width="6"/><rect x="24" y="24" width="32" height="32" rx="3" stroke="var(--prata)" stroke-width="6"/><rect x="27" y="27" width="10" height="10" fill="var(--ouro)"/></svg>lastro</span>`; }

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
      guardar();
      sessao.trocar_senha ? telaTrocaObrigatoria() : telaPrincipal();
    } catch (err) { $("#msg").textContent = err.message; }
  };
}

async function telaPrincipal() {
  $("#app").innerHTML = `<header>${logo()}<div class="linha-btn" style="align-items:center">
      <span class="quem"><b>${esc(sessao.nome)}</b> · ${esc(sessao.papel)} · ${esc(sessao.tenant)}</span>
      <button class="btn sec" id="sair">sair</button></div></header>
    <div class="grade"><aside><div class="abas"><button class="aba ativa" id="aba-dem">demandas</button><button class="aba" id="aba-con">conectores</button><button class="aba" id="aba-conta">conta</button></div><div id="lado"><button class="btn" id="nova">nova demanda</button>
      <p class="rot" style="margin:12px 0 0">demandas</p><div id="lista"></div></div></aside>
    <main id="painel"></main></div>`;
  $("#sair").onclick = sair;
  $("#aba-dem").onclick = () => telaPrincipal();
  $("#aba-con").onclick = () => telaConectores();
  $("#aba-conta").onclick = () => telaConta();
  $("#nova").onclick = () => { atual = null; telaNova(); marcarLista(); };
  await carregarLista();
  const autorizado = new URLSearchParams(location.search).get("autorizado");
  if (autorizado) {  // volta da autorização OAuth2 no sistema do cliente
    history.replaceState(null, "", "/");
    await telaConectores(autorizado);
    if ($("#laudo")) $("#laudo").innerHTML = `<div class="bloco"><p class="ok"><b>Acesso autorizado.</b> O Lastro guardou a autorização no cofre e renova sozinho. Teste agora na "API real do cliente".</p></div>`;
    return;
  }
  if (atual) abrirDemanda(atual); else telaNova();
}

async function carregarLista() {
  const ds = await (await api("/api/demandas")).json();
  $("#lista").innerHTML = ds.length ? ds.map((d) => `<button class="item" data-id="${d.id}"><span>${esc(d.pergunta)}</span><span class="status ${d.status}">${NOMES[d.status] || d.status}</span></button>`).join("")
    : `<p class="quem">Nenhuma demanda ainda. Comece pela primeira pergunta.</p>`;
  document.querySelectorAll(".item").forEach((b) => (b.onclick = () => abrirDemanda(Number(b.dataset.id))));
  marcarLista();
  const problemas = (await (await api("/api/cargas")).json()).filter((k) => k.ultimo_status === "falhou" || k.ultimo_status === "cota");
  if (problemas.length) $("#lista").insertAdjacentHTML("afterbegin", `<button class="aviso-portal" id="b-aviso-cargas"><b>${plural(problemas.length, "carga não atualizou", "cargas não atualizaram")}</b><span>${esc(problemas[0].fonte)}: ${esc(problemas[0].ultimo_aviso)}</span></button>`);
  if ($("#b-aviso-cargas")) $("#b-aviso-cargas").onclick = () => telaConectores(problemas[0].saas);
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
      <p class="quem" style="margin:12px 0 6px">Levar para a nuvem da empresa (o mesmo pipeline, no SQL de cada uma):</p>
      <div class="linha-btn"><button class="btn sec" data-baixar="bigquery">Google BigQuery</button><button class="btn sec" data-baixar="azure">Azure SQL / Fabric</button><button class="btn sec" data-baixar="athena">AWS Athena</button></div>
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
  const a = document.createElement("a"); a.href = url; a.download = `demanda${id}_${NOMES_ARQUIVO[tipo]}`;
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
}

!sessao ? telaLogin() : sessao.trocar_senha ? telaTrocaObrigatoria() : telaPrincipal();

// ---- Conectores: catálogo, teste no sandbox, Postman, importação -------------------------
let catalogo = [];
const PASSOS = ["escolher o sistema", "informar credenciais só de leitura", "testar no sandbox", "conferir no Postman", "conectar à API real", "importar como fonte", "abrir uma demanda"];

async function telaConectores(escolhido) {
  document.querySelectorAll(".aba").forEach((a) => a.classList.toggle("ativa", a.id === "aba-con"));
  catalogo = catalogo.length ? catalogo : await (await api("/api/saas")).json();
  $("#lado").innerHTML = `<p class="rot" style="margin:0">sistemas mapeados</p>` + catalogo.map((c) => `<button class="item" data-saas="${c.id}"><span>${esc(c.nome)}</span><span class="quem">${esc(c.auth)} · ${esc(c.paginacao)} · ${esc(c.limite)}</span></button>`).join("");
  document.querySelectorAll("[data-saas]").forEach((b) => (b.onclick = () => telaConectores(b.dataset.saas)));
  const c = catalogo.find((x) => x.id === escolhido) || catalogo[0];
  document.querySelectorAll("[data-saas]").forEach((b) => b.classList.toggle("ativo", b.dataset.saas === c.id));
  const admin = sessao.papel === "admin";
  $("#painel").innerHTML = `<p class="rot">conector</p><h1>${esc(c.nome)}</h1>
    <ol class="passos">${PASSOS.map((p, i) => `<li${i < 4 ? ' class="feito"' : ""}>${esc(p)}</li>`).join("")}</ol>
    <div id="cargas"></div>
    <h2>Contrato da API</h2>
    <div class="bloco tabela"><table class="contrato"><tbody>
      <tr><th>origem do contrato</th><td>${esc(c.confianca)}</td></tr>
      <tr><th>autenticação</th><td><code>${esc(c.auth)}</code></td></tr>
      <tr><th>paginação</th><td><code>${esc(c.paginacao)}</code>, até ${c.maximo_pagina} por página</td></tr>
      <tr><th>limite</th><td>${esc(c.limite)}</td></tr>
      <tr><th>carga incremental</th><td>${c.incremental ? `<code>${esc(c.incremental)}</code>` : "não tem: carga completa"}</td></tr>
      <tr><th>erro com HTTP 200</th><td>${c.erro_200 ? "sim, o corpo é conferido" : "não"}</td></tr>
    </tbody></table></div>
    ${c.armadilhas.length ? `<h2>Armadilhas conhecidas</h2><div class="bloco"><ul style="margin:0;padding-left:18px;display:grid;gap:6px">${c.armadilhas.map((a) => `<li>${esc(a)}</li>`).join("")}</ul></div>` : ""}
    <h2>Testar conexão</h2>
    ${admin ? `<form class="bloco" id="f-con">
      <div class="duas-col">${[...c.variaveis_url, ...c.campos].map((k) => `<label for="cv-${k}">${esc(k)}<input type="text" id="cv-${k}" data-campo="${k}" data-var="${c.variaveis_url.includes(k) ? 1 : ""}" value="demo"></label>`).join("")}</div>
      <div class="duas-col"><label for="ent">Entidade<select id="ent">${c.entidades.map((e) => `<option>${esc(e)}</option>`).join("")}</select></label>
      ${c.incremental ? `<label for="desde">Só o que mudou desde <small>opcional</small><input type="date" id="desde"></label>` : ""}</div>
      ${c.auth === "oauth2_refresh" ? `<div class="aviso-oauth"><p><b>Este sistema usa autorização (OAuth2).</b> Ninguém digita senha ou token aqui: o admin do cliente entra no ${esc(c.nome)}, autoriza o Lastro só para leitura, e o acesso fica guardado no cofre, renovado sozinho antes de vencer.</p>
        <div class="linha-btn"><button class="btn sec" type="button" id="b-autorizar">autorizar no ${esc(c.nome)}</button></div><p class="erro-msg" id="msg-aut"></p>
        <p class="quem">No sandbox, o teste faz a autorização e uma renovação de token simuladas.</p></div>` : ""}
      <fieldset class="modo"><legend class="rot">onde testar</legend>
        <label><input type="radio" name="modo" value="sandbox" checked> sandbox do Lastro <small>simula a API com as armadilhas reais; nenhum dado sai daqui</small></label>
        <label><input type="radio" name="modo" value="real"> API real do cliente <small>use credencial somente leitura; a rede do servidor precisa alcançar o sistema</small></label></fieldset>
      <div class="linha-btn"><button class="btn ouro" type="submit" value="testar">testar conexão</button><button class="btn sec" type="submit" value="importar">testar e importar como fonte</button><button class="btn sec" type="button" id="b-postman">baixar coleção do Postman</button></div>
      <p class="quem">No Postman: importe a coleção e rode na ordem. Ela já aponta para o sandbox deste servidor e testa as armadilhas do contrato.</p>
    </form><div id="laudo"></div>` : `<p class="quem">Só o admin da empresa conecta sistemas.</p>`}`;
  cargasHtml();
  if (!admin) return;
  if ($("#b-autorizar")) $("#b-autorizar").onclick = async () => {
    try { location.href = (await (await api(`/api/saas/${c.id}/oauth/iniciar`)).json()).url; }
    catch (err) { $("#msg-aut").textContent = err.message; }
  };
  $("#b-postman").onclick = async () => {
    const r = await api(`/api/saas/${c.id}/postman`);
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement("a"); a.href = url; a.download = `lastro-${c.id}.postman_collection.json`; document.body.append(a); a.click(); a.remove();
  };
  $("#f-con").onsubmit = async (e) => {
    e.preventDefault();
    const cred = {}, vars = {};
    document.querySelectorAll("[data-campo]").forEach((i) => ((i.dataset.var ? vars : cred)[i.dataset.campo] = i.value));
    const corpo = { entidade: $("#ent").value, credenciais: cred, variaveis: vars, desde: $("#desde")?.value || null,
      modo: document.querySelector("[name=modo]:checked").value, importar: e.submitter?.value === "importar" };
    $("#laudo").innerHTML = `<div class="bloco"><p class="quem">conectando…</p></div>`;
    try {
      const l = await (await api(`/api/saas/${c.id}/testar`, { method: "POST", json: corpo })).json();
      $("#laudo").innerHTML = laudoHtml(l) + (l.fonte_id ? agendarHtml(c) : "");
      if (l.fonte_id && $("#f-agendar")) $("#f-agendar").onsubmit = (ev) => agendar(ev, c, corpo, l.fonte_id);
    }
    catch (err) { $("#laudo").innerHTML = `<div class="bloco"><p class="erro-msg">${esc(err.message)}</p></div>`; }
  };
}

function agendarHtml(c) {
  const horas = Array.from({ length: 24 }, (_, h) => `<option value="${h}"${h === 6 ? " selected" : ""}>${String(h).padStart(2, "0")}h</option>`).join("");
  return `<form class="bloco" id="f-agendar"><h3 style="margin:0">Manter esta fonte atualizada</h3>
    <p class="quem">Todo dia, o Lastro busca só o que mudou desde a última carga boa. Se der erro ou a cota do contrato acabar, nada é alterado e o aviso aparece aqui. Plano Operação.</p>
    <div class="duas-col"><label for="ag-hora">Horário (Brasília)<select id="ag-hora">${horas}</select></label>
    ${c.pacotes.length ? `<label for="ag-pacote">Pacote do contrato <small>define a cota diária</small><select id="ag-pacote"><option value="">não sei / sem cota</option>${c.pacotes.map((p) => `<option>${esc(p)}</option>`).join("")}</select></label>` : ""}</div>
    <div class="linha-btn"><button class="btn ouro" type="submit">agendar carga diária</button></div><p class="erro-msg" id="msg-ag"></p></form>`;
}

async function agendar(e, c, corpo, fonteId) {
  e.preventDefault();
  try {
    const r = await (await api("/api/cargas", { method: "POST", json: { fonte_id: fonteId, saas: c.id, entidade: corpo.entidade, variaveis: corpo.variaveis,
      credenciais: corpo.credenciais, modo: corpo.modo, hora: Number($("#ag-hora").value), pacote: $("#ag-pacote")?.value || null } })).json();
    $("#f-agendar").outerHTML = `<div class="bloco"><p class="ok"><b>Carga agendada.</b> Todo dia às ${String(r.hora).padStart(2, "0")}h${r.cota_diaria ? `, até ${r.cota_diaria} requisições por dia` : ""}.</p></div>`;
    cargasHtml();
  } catch (err) { $("#msg-ag").textContent = err.message; }
}

const STATUS_CARGA = { nunca: "ainda não rodou", ok: "atualizada", falhou: "falhou", cota: "cota esgotada" };
const quando = (t) => t ? new Date(t * 1000).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "—";

async function cargasHtml() {
  const alvo = $("#cargas");
  if (!alvo) return;
  const cs = await (await api("/api/cargas")).json();
  alvo.innerHTML = cs.length ? `<h2>Cargas agendadas</h2><div class="bloco tabela"><table><thead><tr><th>fonte</th><th>horário</th><th>situação</th><th>última carga boa</th><th>requisições hoje</th></tr></thead><tbody>
    ${cs.map((k) => `<tr><td>${esc(k.fonte)}</td><td>${String(k.hora).padStart(2, "0")}h</td><td><span class="status ${k.ultimo_status === "ok" ? "aprovada" : k.ultimo_status === "nunca" ? "" : "reprovada"}">${STATUS_CARGA[k.ultimo_status]}</span></td><td>${quando(k.marca_dagua)}</td><td>${k.chamadas_no_dia}${k.cota_diaria ? " de " + k.cota_diaria : ""}</td></tr>
      ${k.ultimo_aviso ? `<tr><td colspan="5" class="aviso-carga">${esc(k.ultimo_aviso)}</td></tr>` : ""}`).join("")}</tbody></table></div>` : "";
}

function laudoHtml(l) {
  if (!l.ok) return `<div class="bloco"><p class="erro"><b>Falhou:</b> ${esc(l.erro)}</p><p>${esc(l.mensagem)}</p><p class="quem">${l.chamadas ?? l.requisicoes_no_sandbox ?? 0} requisições · ${l.duracao_s}s</p></div>`;
  const cols = l.colunas.slice(0, 8);
  return `<div class="bloco"><p><span class="status aprovada">conexão ok · ${esc(l.modo)}</span></p>
    <div class="numeros"><div><span class="rot">registros</span><b>${num(l.registros)}</b></div><div><span class="rot">total da API</span><b>${l.total_informado ?? "—"}</b></div><div><span class="rot">requisições</span><b>${l.chamadas}</b></div><div><span class="rot">429 absorvidos</span><b>${l.tentativas_429}</b></div><div><span class="rot">tempo real estimado</span><b>${l.tempo_real_estimado_s != null ? l.tempo_real_estimado_s + "s" : "—"}</b></div></div>
    <p class="quem">truncamento ${esc(l.truncamento)} · ${plural((l.renovacoes_token || 0) + l.relogins, "renovação", "renovações")} de token · ${l.tentativas_escrita_bloqueadas ?? 0} tentativas de escrita bloqueadas${l.avisos.length ? " · " + esc(l.avisos.join("; ")) : ""}</p>
    ${l.fonte_id ? `<p class="ok"><b>Importado como fonte.</b> Já aparece em "nova demanda".</p>` : ""}
    <div class="tabela"><table><thead><tr>${cols.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${l.amostra.map((r) => `<tr>${cols.map((c) => `<td>${esc(typeof r[c] === "object" ? JSON.stringify(r[c]) : r[c])}</td>`).join("")}</tr>`).join("")}</tbody></table></div></div>`;
}

// ---- Conta: trocar a própria senha; admin cadastra a equipe (LST-32) -------------------
const PAPEIS = { demandante: "demandante", revisor: "revisor de negócio", leitor: "leitor", admin: "admin" };

function formSenha(titulo, atualRotulo) {
  return `<form class="bloco" id="f-senha"><h2>${titulo}</h2>
    <label for="s-atual">${atualRotulo}<input id="s-atual" type="password" required autocomplete="current-password"></label>
    <label for="s-nova">Nova senha <small>no mínimo 12 caracteres</small><input id="s-nova" type="password" required minlength="12" autocomplete="new-password"></label>
    <label for="s-conf">Repita a nova senha<input id="s-conf" type="password" required minlength="12" autocomplete="new-password"></label>
    <button class="btn" type="submit">trocar senha</button><p class="erro-msg" id="s-msg" role="status"></p></form>`;
}

function ligarFormSenha(depois) {
  $("#f-senha").onsubmit = async (e) => {
    e.preventDefault();
    const msg = $("#s-msg");
    if ($("#s-nova").value !== $("#s-conf").value) { msg.textContent = "As duas senhas novas não batem."; return; }
    try {
      const r = await (await api("/api/conta/senha", { method: "POST", json: { atual: $("#s-atual").value, nova: $("#s-nova").value } })).json();
      sessao = { ...sessao, token: r.token, trocar_senha: false };
      guardar();
      depois();
    } catch (err) { msg.textContent = err.message; }
  };
}

function telaTrocaObrigatoria() {
  $("#app").innerHTML = `<div class="login"><div style="display:grid;gap:12px;width:min(420px,100%)">${logo()}
    <p class="quem">Olá, ${esc(sessao.nome)}. Você entrou com uma senha provisória. Escolha a sua para continuar.</p>
    ${formSenha("Crie sua senha", "Senha provisória")}<button class="btn sec" id="sair">sair</button></div></div>`;
  $("#sair").onclick = sair;
  ligarFormSenha(() => telaPrincipal());
}

async function telaConta() {
  document.querySelectorAll(".aba").forEach((a) => a.classList.toggle("ativa", a.id === "aba-conta"));
  const admin = sessao.papel === "admin";
  $("#lado").innerHTML = `<p class="quem"><b>${esc(sessao.nome)}</b><br>${esc(sessao.papel)} · ${esc(sessao.tenant)}</p>`;
  $("#painel").innerHTML = formSenha("Trocar minha senha", "Senha atual") + (admin ? `<div id="equipe"></div>` : "");
  ligarFormSenha(() => { $("#s-msg").className = "ok"; $("#s-msg").textContent = "Senha trocada."; $("#f-senha").reset(); });
  if (admin) await telaEquipe();
}

async function telaEquipe(nova = null) {
  const us = await (await api("/api/usuarios")).json();
  $("#equipe").innerHTML = `<div class="bloco"><h2>Equipe</h2>
    <p class="quem">Cadastre quem vai usar o Lastro na sua empresa. A pessoa recebe uma senha provisória e escolhe a dela no primeiro acesso. Esqueceu a senha? Cadastre o mesmo e-mail de novo para gerar outra.</p>
    <div class="tabela"><table><thead><tr><th>nome</th><th>e-mail</th><th>papel</th><th>senha</th></tr></thead><tbody>
    ${us.map((u) => `<tr><td>${esc(u.nome)}</td><td>${esc(u.email)}</td><td>${esc(PAPEIS[u.papel] || u.papel)}</td><td class="${u.trocar_senha ? "aviso" : "quem"}">${u.trocar_senha ? "provisória" : "definida"}</td></tr>`).join("")}
    </tbody></table></div>
    ${nova ? `<div class="bloco" style="background:var(--sup-2)"><p><b>Senha provisória de ${esc(nova.email)}</b> (aparece só agora; passe por um canal privado):</p>
      <div class="linha-btn" style="align-items:center"><code id="prov">${esc(nova.senha_provisoria)}</code><button class="btn sec" id="copiar" type="button">copiar</button></div></div>` : ""}
    <form id="f-conv" class="duas-col" style="align-items:end">
      <label for="c-nome">Nome<input id="c-nome" type="text" required></label>
      <label for="c-email">E-mail<input id="c-email" type="email" required></label>
      <label for="c-papel">Papel<select id="c-papel">${Object.entries(PAPEIS).map(([k, v]) => `<option value="${k}">${v}</option>`).join("")}</select></label>
      <button class="btn" type="submit">cadastrar</button></form><p class="erro-msg" id="c-msg" role="status"></p></div>`;
  if (nova) $("#copiar").onclick = async () => {
    try { await navigator.clipboard.writeText(nova.senha_provisoria); $("#copiar").textContent = "copiada"; }
    catch { const r = document.createRange(); r.selectNodeContents($("#prov")); const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); }
  };
  $("#f-conv").onsubmit = async (e) => {
    e.preventDefault();
    try {
      const r = await (await api("/api/usuarios", { method: "POST", json: { nome: $("#c-nome").value, email: $("#c-email").value, papel: $("#c-papel").value } })).json();
      await telaEquipe(r);
    } catch (err) { $("#c-msg").textContent = err.message; }
  };
}
