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
  if (r.status === 401 && cab.Authorization) { sair(); throw new Error("Sua sessão expirou. Entre de novo."); }
  if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Erro ${r.status}`); }
  return r;
}

function guardar() { try { sessionStorage.setItem("lastro", JSON.stringify(sessao)); } catch {} }

function sair() { sessao = null; try { sessionStorage.removeItem("lastro"); } catch {} telaLogin(); }

function logo() { return `<span class="logo"><svg width="22" height="22" viewBox="0 0 64 64" fill="none" aria-hidden="true"><rect x="8" y="8" width="32" height="32" rx="3" stroke="var(--tinta)" stroke-width="6"/><rect x="24" y="24" width="32" height="32" rx="3" stroke="var(--prata)" stroke-width="6"/><rect x="27" y="27" width="10" height="10" fill="var(--ouro)"/></svg>lastro</span>`; }

let contasDemo = null;  // /api/config: contas de demonstração só fora de produção (LST-55, A5)

async function telaLogin(msg = "") {
  if (contasDemo === null) {
    try { contasDemo = Boolean((await (await fetch("/api/config")).json()).contas_demo); } catch { contasDemo = false; }
  }
  $("#app").innerHTML = `<div class="login"><form class="bloco" id="f-login" novalidate>
    ${logo()}
    <div><h1>Entrar</h1><p class="quem">Cada empresa tem o seu espaço. Você só vê os dados da sua.</p></div>
    <label for="email">E-mail<input id="email" type="email" required ${contasDemo ? 'value="ana@demo.lastro"' : ""} autocomplete="username"></label>
    <label for="senha">Senha<input id="senha" type="password" required ${contasDemo ? 'value="demo1234"' : ""} autocomplete="current-password"></label>
    <button class="btn" type="submit" id="b-entrar">entrar</button>
    <p class="erro-msg" id="msg" role="alert">${esc(msg)}</p>
    ${contasDemo ? '<div class="dica">Contas de teste (senha demo1234):<br>ana@demo.lastro · demandante<br>rui@demo.lastro · revisor de negócio<br>admin@demo.lastro · admin</div>' : ""}
  </form></div>`;
  $("#f-login").onsubmit = async (e) => {
    e.preventDefault();
    const b = $("#b-entrar");
    if (!$("#email").value.trim() || !$("#senha").value) { $("#msg").textContent = "Preencha o e-mail e a senha."; return; }
    b.disabled = true; b.textContent = "entrando…"; $("#msg").textContent = "";
    try {
      const r = await api("/api/login", { method: "POST", json: { email: $("#email").value.trim(), senha: $("#senha").value } });
      sessao = await r.json();
      guardar();
      sessao.trocar_senha ? telaTrocaObrigatoria() : telaPrincipal();
    } catch (err) {
      $("#msg").textContent = /inválid/.test(err.message) ? "E-mail ou senha não conferem. Confira e tente de novo." : err.message;
      b.disabled = false; b.textContent = "entrar"; $("#senha").select();
    }
  };
}

async function telaPrincipal() {
  $("#app").innerHTML = `<header>${logo()}<div class="linha-btn" style="align-items:center">
      <span class="quem"><b>${esc(sessao.nome)}</b><span class="papel"> · ${esc(sessao.papel)} · ${esc(sessao.tenant)}</span></span>
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
  if (autorizado === "planilha_bi") {  // volta do Google: a planilha do BI (LST-48) já recebeu o primeiro envio
    history.replaceState(null, "", "/");
    await telaConta();
    if ($("#bi-msg")) { $("#bi-msg").className = "ok"; $("#bi-msg").textContent = "Google autorizado. A planilha recebe as tabelas prontas a cada publicação."; }
    return;
  }
  if (autorizado) {  // volta da autorização OAuth2 no sistema do cliente
    history.replaceState(null, "", "/");
    await telaConectores(autorizado);
    if ($("#laudo")) $("#laudo").innerHTML = `<div class="bloco"><p class="ok"><b>Acesso autorizado.</b> O Lastro guardou a autorização no cofre e renova sozinho. Teste agora na "API real do cliente".</p></div>`;
    return;
  }
  if (atual) abrirDemanda(atual); else telaNova();
}

async function carregarLista() {
  let ds;
  try { ds = await (await api("/api/demandas")).json(); }
  catch (err) {
    $("#lista").innerHTML = `<p class="erro-msg" role="alert">${esc(err.message)}</p><button class="btn sec" id="b-lista-de-novo">tentar de novo</button>`;
    $("#b-lista-de-novo").onclick = carregarLista;
    return;
  }
  $("#lista").innerHTML = ds.length ? ds.map((d) => `<button class="item" data-id="${d.id}"><span>${esc(d.pergunta)}</span><span class="status ${d.status}">${NOMES[d.status] || d.status}</span></button>`).join("")
    : `<p class="quem">Nenhuma demanda ainda. Comece pela primeira pergunta.</p>`;
  document.querySelectorAll(".item").forEach((b) => (b.onclick = () => abrirDemanda(Number(b.dataset.id))));
  marcarLista();
  let problemas = [];
  try { problemas = (await (await api("/api/cargas")).json()).filter((k) => k.ultimo_status === "falhou" || k.ultimo_status === "cota"); } catch { /* o aviso de cargas é extra */ }
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

const suave = () => (matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth");

async function abrirDemanda(id) {
  atual = id; marcarLista();
  const p = $("#painel");
  p.setAttribute("aria-busy", "true");
  p.innerHTML = `<p class="rot">demanda ${id}</p><div class="bloco esqueleto" style="height:120px"></div><div class="bloco esqueleto" style="height:220px"></div>`;
  let d;
  try { d = await (await api(`/api/demandas/${id}`)).json(); }
  catch (err) {
    p.innerHTML = `<p class="rot">demanda ${id}</p><div class="bloco"><p class="erro-msg" role="alert">Não consegui abrir esta demanda: ${esc(err.message)}</p><div class="linha-btn"><button class="btn sec" id="b-de-novo">tentar de novo</button></div></div>`;
    $("#b-de-novo").onclick = () => abrirDemanda(id);
    return;
  } finally { p.removeAttribute("aria-busy"); }
  let html = `<p class="rot">demanda ${d.id} · <span class="status ${d.status}">${NOMES[d.status] || d.status}</span></p><h1>${esc(d.pergunta)}</h1>`;
  if (d.status === "grill") html += grillHtml(d);
  if (d.status === "pronta") html += `<div class="bloco"><p>Grill respondido. Os agentes vão modelar, construir o pipeline no sandbox, responder e auditar.</p><div class="linha-btn"><button class="btn ouro" id="b-exec">rodar agentes</button></div><p class="erro-msg" id="msg"></p></div>`;
  if (d.resposta) html += resultadoHtml(d);
  if (d.status === "aprovada") html += `<div id="painel-dem"></div><div id="conversa-dem"></div>`;
  if (d.eventos?.length) html += `<h2>Rastro dos agentes</h2><div class="bloco rastro">${d.eventos.map((e) => `<div><b>${esc(e.ator.split("@")[0])}</b><span>${esc(e.acao)} · ${esc(e.detalhe.slice(0, 220))}</span></div>`).join("")}</div>`;
  p.innerHTML = html;
  if (matchMedia("(max-width: 760px)").matches) p.scrollIntoView({ block: "start", behavior: suave() });  // no celular a lista fica acima (A4)
  if ($("#f-grill")) $("#f-grill").onsubmit = (e) => enviarGrill(e, d);
  if ($("#b-exec")) $("#b-exec").onclick = () => executar(d.id);
  document.querySelectorAll("[data-baixar]").forEach((b) => (b.onclick = () => baixar(d.id, b.dataset.baixar)));
  if ($("#f-rev")) $("#f-rev").onsubmit = (e) => revisar(e, d.id);
  if ($("#painel-dem")) await telaPainel(d.id);
  if ($("#conversa-dem")) await telaConversa(d.id);
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
  const exporta = admin || sessao.papel === "demandante";
  $("#painel").innerHTML = formSenha("Trocar minha senha", "Senha atual") + (admin ? `<div id="bi"></div><div id="equipe"></div>` : "") + (exporta && !admin ? `<div id="exportar"></div>` : "");
  ligarFormSenha(() => { $("#s-msg").className = "ok"; $("#s-msg").textContent = "Senha trocada."; $("#f-senha").reset(); });
  if (admin) { await telaBI(); await telaEquipe(); } else if (exporta) await telaExportar($("#exportar"));
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

// ---- Levar os dados para o BI (LST-33) ---------------------------------------------------
async function copiar(botao, texto, alvo) {
  try { await navigator.clipboard.writeText(texto); botao.textContent = "copiado"; }
  catch { const r = document.createRange(); r.selectNodeContents(alvo); const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); }
}

async function baixarArquivo(caminho, botao) {
  const antes = botao.textContent; botao.disabled = true; botao.textContent = "gerando…";
  try {
    const r = await api(caminho);
    const nome = (r.headers.get("content-disposition") || "").match(/filename="([^"]+)"/)?.[1] || "fonte";
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement("a"); a.href = url; a.download = nome; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  } catch (err) { alert(err.message); }
  finally { botao.disabled = false; botao.textContent = antes; }
}

async function telaExportar(alvo) {
  const fs = (await (await api("/api/fontes")).json()).filter((f) => f.tipo === "arquivo");
  alvo.innerHTML = `<div class="bloco"><h2>Exportar fontes</h2>
    <p class="quem">Uma cópia de cada fonte em CSV (Excel, Looker Studio por upload, Google Sheets) ou Parquet (Power BI, Python). A fonte original não é alterada.</p>
    ${fs.length ? `<div class="tabela"><table><tbody>${fs.map((f) => `<tr><td>${esc(f.nome)}</td><td style="text-align:right"><div class="linha-btn" style="justify-content:flex-end">
      <button class="btn sec" data-exp="${f.id}" data-fmt="csv">csv</button><button class="btn sec" data-exp="${f.id}" data-fmt="parquet">parquet</button></div></td></tr>`).join("")}</tbody></table></div>`
      : `<p class="quem">Nenhuma fonte de arquivo ainda.</p>`}</div>`;
  alvo.querySelectorAll("[data-exp]").forEach((b) => (b.onclick = () => baixarArquivo(`/api/fontes/${b.dataset.exp}/exportar?formato=${b.dataset.fmt}`, b)));
}

const quandoBI = (iso) => iso ? new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "ainda não";

async function telaBI(nova = null, teste = null, chave = null) {
  const alvo = $("#bi");
  const e = await (await api("/api/bi")).json();
  let html = `<div class="bloco"><h2>Conectar ao BI</h2>`;
  if (!e.disponivel) {
    html += `<p class="quem">${esc(e.motivo)}. Enquanto isso, exporte as fontes em CSV ou Parquet abaixo.</p>`;
  } else if (!e.ligado) {
    html += `<p class="quem">Liga um acesso só de leitura ao banco do Lastro, com as suas fontes e o resultado das demandas aprovadas, para usar no Power BI, no Looker Studio, no Metabase ou em qualquer BI que conecte em PostgreSQL. Só a sua empresa aparece nesse acesso, e ele não altera nada.</p>
      <div class="linha-btn"><button class="btn" id="bi-ligar">ligar o BI</button></div>`;
  } else {
    const c = e.conexao;
    const linhas = [["Servidor", c.host], ["Porta", c.porta], ["Banco", c.banco], ["Usuário", c.usuario], ["SSL", c.ssl]];
    html += `<p class="quem">Use estes dados no conector <b>PostgreSQL</b> do seu BI. Atualizado ${esc(quandoBI(e.publicado_em))}; o Lastro atualiza sozinho depois de cada carga e de cada demanda aprovada.</p>
      ${teste ? `<p class="${teste.ok ? "ok" : "erro"}"><b>${teste.ok ? "Testado:" : "Atenção:"}</b> ${esc(teste.detalhe)}</p>` : ""}
      ${nova ? `<div class="bloco" style="background:var(--sup-2)"><p><b>Senha do BI</b> (aparece só agora; guarde no gerenciador de senhas ou cole direto no BI):</p>
        <div class="linha-btn" style="align-items:center"><code id="bi-senha" style="overflow-wrap:anywhere">${esc(nova.senha)}</code><button class="btn sec" id="bi-copiar-senha" type="button">copiar</button></div></div>` : ""}
      <div class="tabela"><table class="contrato"><tbody>${linhas.map(([k, v], i) => `<tr><th>${k}</th><td><code id="bi-v${i}">${esc(v)}</code></td><td style="text-align:right"><button class="btn sec" data-copia="${i}">copiar</button></td></tr>`).join("")}</tbody></table></div>
      <h2 style="margin:6px 0 0">Tabelas no BI</h2>
      ${e.tabelas.length ? `<div class="tabela"><table><thead><tr><th>tabela</th><th>de onde vem</th><th>linhas</th></tr></thead><tbody>${e.tabelas.map((t) => `<tr><td><code>${esc(t.tabela)}</code></td><td>${esc(t.origem)}</td><td class="n">${t.mantida ? "mantida (arquivo fora do servidor)" : num(t.linhas)}</td></tr>`).join("")}</tbody></table></div>`
        : `<p class="quem">Nada publicado ainda. Envie uma fonte ou aprove uma demanda e clique em publicar.</p>`}
      <p class="erro-msg" id="bi-msg" role="status"></p>
      <div class="linha-btn"><button class="btn" id="bi-publicar">publicar agora</button><button class="btn sec" id="bi-trocar">trocar a senha</button><button class="btn sec" id="bi-desligar">desligar</button></div>
      <h2 style="margin:6px 0 0">Power BI sem certificado e sem gateway (recomendado)</h2>
      <p class="quem">O projeto do Power BI baixado no painel da demanda lê estas tabelas pela internet, com uma <b>chave de leitura</b>: não precisa do certificado do banco nem de gateway, e a atualização agendada funciona no Power BI Service. Chave ${e.chave_ativa ? `ativa desde ${esc(quandoBI(e.chave_criada_em))}, último uso ${esc(quandoBI(e.chave_usada_em))}` : "ainda não gerada"}.</p>
      ${chave ? `<div class="bloco" style="background:var(--sup-2)"><p><b>Chave de leitura</b> (aparece só agora; cole no parâmetro <code>ChaveLastro</code> do projeto e guarde como senha):</p>
        <div class="linha-btn" style="align-items:center"><code id="bi-chave" style="overflow-wrap:anywhere">${esc(chave.chave)}</code><button class="btn sec" id="bi-copiar-chave" type="button">copiar</button></div>
        <p class="quem">Endereço: <code>${esc(chave.base)}</code> · cabeçalho <code>${esc(chave.cabecalho)}</code></p></div>` : ""}
      <h2 style="margin:6px 0 0">Data Studio pela planilha Google</h2>
      ${e.planilha?.autorizada
        ? `<p class="quem">As tabelas prontas (<code>painel_…</code>) vão para uma planilha no <b>seu</b> Google Drive a cada publicação; no Data Studio use o conector <b>Planilhas Google</b>, sem senha de banco nem certificado. ${e.planilha.url ? `Última atualização ${esc(quandoBI(e.planilha.enviada_em))}: <a href="${esc(e.planilha.url)}" target="_blank" rel="noopener">abrir a planilha</a>.` : "Ainda não enviada."}</p>
           <div class="linha-btn"><button class="btn sec" id="bi-planilha-enviar">enviar agora</button><button class="btn sec" id="bi-planilha-sair">desconectar</button></div>`
        : `<p class="quem">Quer o Data Studio sem senha de banco nem certificado? Autorize o Google uma vez: o Lastro cria uma planilha no seu Drive e só enxerga essa planilha (permissão <i>drive.file</i>).</p>
           <div class="linha-btn"><button class="btn sec" id="bi-planilha-autorizar">conectar minha conta Google</button></div>`}
      <div class="linha-btn"><button class="btn sec" id="bi-chave-gerar">${e.chave_ativa ? "trocar a chave" : "gerar a chave de leitura"}</button>${e.chave_ativa ? `<button class="btn sec" id="bi-chave-revogar">revogar a chave</button>` : ""}</div>
      <details><summary>Como conectar (Power BI, Looker Studio, Metabase)</summary><ul class="quem">
        <li><b>Power BI Desktop</b> (gratuito): Obter dados → Banco de dados PostgreSQL → servidor <code>${esc(c.host)}:${esc(c.porta)}</code>, banco <code>${esc(c.banco)}</code> → usuário e senha acima. As tabelas <code>d…_fato</code> e <code>d…_dim_…</code> já formam um esquema estrela.</li>
        <li><b>Looker Studio</b>: Adicionar dados → PostgreSQL → preencha os campos acima e marque "Ativar SSL".</li>
        <li><b>Metabase</b>: Admin → Bancos de dados → Adicionar → PostgreSQL, com os mesmos dados e SSL.</li></ul></details>`;
  }
  alvo.innerHTML = html + `</div><div id="exportar"></div>`;
  await telaExportar($("#exportar"));
  const acao = async (botao, fazer) => { botao.disabled = true; try { await fazer(); } catch (err) { $("#bi-msg") ? ($("#bi-msg").textContent = err.message) : alert(err.message); botao.disabled = false; } };
  if ($("#bi-ligar")) $("#bi-ligar").onclick = (ev) => acao(ev.target, async () => { const r = await (await api("/api/bi/credencial", { method: "POST" })).json(); await telaBI(r.credencial, r.teste); });
  if (!e.ligado) return;
  document.querySelectorAll("[data-copia]").forEach((b) => (b.onclick = () => copiar(b, $(`#bi-v${b.dataset.copia}`).textContent, $(`#bi-v${b.dataset.copia}`))));
  if (nova) $("#bi-copiar-senha").onclick = (ev) => copiar(ev.target, nova.senha, $("#bi-senha"));
  $("#bi-publicar").onclick = (ev) => acao(ev.target, async () => { const r = await (await api("/api/bi/publicar", { method: "POST" })).json(); await telaBI(); if (r.avisos.length) $("#bi-msg").textContent = r.avisos.join(" · "); });
  $("#bi-trocar").onclick = (ev) => acao(ev.target, async () => { const r = await (await api("/api/bi/credencial", { method: "POST" })).json(); await telaBI(r.credencial, r.teste); });
  if ($("#bi-planilha-autorizar")) $("#bi-planilha-autorizar").onclick = (ev) => acao(ev.target, async () => { location.href = (await (await api("/api/bi/planilha/autorizar", { method: "POST" })).json()).url; });
  if ($("#bi-planilha-enviar")) $("#bi-planilha-enviar").onclick = (ev) => acao(ev.target, async () => { const r = await (await api("/api/bi/planilha/enviar", { method: "POST" })).json(); await telaBI(); $("#bi-msg").className = "ok"; $("#bi-msg").textContent = `Planilha atualizada: ${r.abas.length} aba(s).` + (r.avisos.length ? " " + r.avisos.join(" · ") : ""); });
  if ($("#bi-planilha-sair")) $("#bi-planilha-sair").onclick = (ev) => {
    const b = ev.target;
    if (b.dataset.confirmar !== "1") { b.dataset.confirmar = "1"; b.textContent = "confirmar: a planilha para de atualizar"; return; }
    acao(b, async () => { await api("/api/bi/planilha", { method: "DELETE" }); await telaBI(); });
  };
  if (chave) $("#bi-copiar-chave").onclick = (ev) => copiar(ev.target, chave.chave, $("#bi-chave"));
  $("#bi-chave-gerar").onclick = (ev) => acao(ev.target, async () => { const r = await (await api("/api/bi/chave", { method: "POST" })).json(); await telaBI(null, null, r); });
  if ($("#bi-chave-revogar")) $("#bi-chave-revogar").onclick = (ev) => {
    const b = ev.target;
    if (b.dataset.confirmar !== "1") { b.dataset.confirmar = "1"; b.textContent = "confirmar: o Power BI para de atualizar"; return; }
    acao(b, async () => { await api("/api/bi/chave", { method: "DELETE" }); await telaBI(); });
  };
  $("#bi-desligar").onclick = (ev) => {
    const b = ev.target;
    if (b.dataset.confirmar !== "1") { b.dataset.confirmar = "1"; b.textContent = "confirmar: o BI perde o acesso"; return; }
    acao(b, async () => { await api("/api/bi/credencial", { method: "DELETE" }); await telaBI(); });
  };
}

// ---- Painel da demanda (LST-34) -----------------------------------------------------------
const TIPOS_VISUAL = { kpi: "número (KPI)", barras: "barras", linha: "linha no tempo", tabela: "tabela" };
const AGREG = { soma: "soma", media: "média", contagem: "contagem", distintos: "distintos", minimo: "mínimo", maximo: "máximo" };

async function telaPainel(did, aviso = "") {
  const alvo = $("#painel-dem");
  const pode = ["admin", "demandante"].includes(sessao.papel);
  const e = await (await api(`/api/demandas/${did}/painel`)).json();
  if (!e.spec) {
    alvo.innerHTML = `<h2>Painel</h2><div class="bloco"><p class="quem">O designer do Lastro monta um painel com o resultado aprovado: o número principal, a quebra que você pediu e a evolução no tempo. Ele sai em HTML (abre em qualquer navegador) e como projeto do Power BI, ligado ao BI da sua empresa.</p>
      ${pode ? `<div class="linha-btn"><button class="btn ouro" id="p-criar">montar painel</button></div>` : `<p class="quem">Quem demanda ou o admin pode montar o painel.</p>`}<p class="erro-msg" id="p-msg"></p></div>`;
    if ($("#p-criar")) $("#p-criar").onclick = async (ev) => { ev.target.disabled = true; try { await api(`/api/demandas/${did}/painel`, { method: "POST" }); await abrirDemanda(did); } catch (err) { $("#p-msg").textContent = err.message; ev.target.disabled = false; } };
    return;
  }
  const s = e.spec, med = Object.fromEntries(s.medidas.map((m) => [m.id, m]));
  const opts = (lista, rot = (x) => x) => lista.map((x) => `<option value="${esc(x)}">${esc(rot(x))}</option>`).join("");
  alvo.innerHTML = `<h2>Painel <span class="quem">· versão ${s.versao} de ${e.versoes.length}</span></h2>
    <div class="bloco">
      <iframe id="p-previa" title="Prévia do painel" style="width:100%;height:520px;border:1px solid var(--linha);border-radius:8px;background:var(--sup)"></iframe>
      <div class="linha-btn"><button class="btn sec" id="p-html">baixar HTML</button><button class="btn sec" id="p-pbi">baixar projeto do Power BI</button><button class="btn sec" id="p-rel">relatório de entrega (Power BI)</button></div>
      <div class="tabela"><table><thead><tr><th>visual</th><th>tipo</th><th>medida</th><th>eixo</th>${pode ? "<th></th>" : ""}</tr></thead><tbody>
        ${s.visuais.map((v) => `<tr><td><code>${esc(v.id)}</code> ${esc(v.titulo)}</td><td>${esc(TIPOS_VISUAL[v.tipo] || v.tipo)}</td><td>${esc(med[v.medida]?.nome || v.medida)}</td><td>${esc(v.eixo || "—")}</td>${pode ? `<td style="text-align:right"><button class="btn sec" data-rem="${esc(v.id)}">remover</button></td>` : ""}</tr>`).join("")}
      </tbody></table></div>
      ${pode ? `<form id="p-pedir" style="display:grid;gap:8px"><label for="p-texto">Peça uma mudança ao designer <small>ex.: "adicione um gráfico de barras de valor vendido por estado", "nova medida média de valor orçado", "remova o v3"</small>
        <input id="p-texto" type="text" required></label><div class="linha-btn"><button class="btn" type="submit">pedir</button></div></form>
      <details><summary>ou monte pelo formulário</summary>
        <form id="p-visual" class="duas-col" style="align-items:end;margin-top:10px">
          <label for="p-tipo">Visual<select id="p-tipo">${opts(e.opcoes.tipos, (x) => TIPOS_VISUAL[x] || x)}</select></label>
          <label for="p-med">Medida<select id="p-med">${opts(s.medidas.map((m) => m.id), (x) => med[x].nome)}</select></label>
          <label for="p-eixo">Eixo<select id="p-eixo"><option value="">— (KPI)</option>${opts(e.opcoes.eixos)}</select></label>
          <button class="btn" type="submit">adicionar visual</button></form>
        <form id="p-medida" class="duas-col" style="align-items:end;margin-top:10px">
          <label for="p-agg">Agregação<select id="p-agg">${opts(e.opcoes.agregacoes, (x) => AGREG[x] || x)}</select></label>
          <label for="p-col">Coluna<select id="p-col">${opts(e.opcoes.colunas)}</select></label>
          <button class="btn" type="submit">adicionar medida</button></form></details>` : ""}
      <p class="${aviso.startsWith("ok:") ? "ok" : "erro-msg"}" id="p-msg" role="status">${esc(aviso.replace(/^ok:/, ""))}</p>
    </div>`;
  try { $("#p-previa").srcdoc = await (await api(`/api/demandas/${did}/painel/html`)).text(); } catch { /* prévia é conveniência */ }
  $("#p-html").onclick = (ev) => baixarArquivo(`/api/demandas/${did}/painel/html`, ev.target);
  $("#p-pbi").onclick = (ev) => baixarArquivo(`/api/demandas/${did}/painel/powerbi`, ev.target);
  $("#p-rel").onclick = (ev) => baixarArquivo(`/api/demandas/${did}/relatorio/powerbi`, ev.target);
  if (!pode) return;
  const mudar = async (corpo) => {
    try { const r = await (await api(`/api/demandas/${did}/painel/mudancas`, { method: "POST", json: corpo })).json(); await abrirDemanda(did); await telaPainel(did, `ok:Versão ${r.versao} gravada no rastro.`); }
    catch (err) { $("#p-msg").className = "erro-msg"; $("#p-msg").textContent = err.message; }
  };
  $("#p-pedir").onsubmit = (ev) => { ev.preventDefault(); mudar({ pedido: $("#p-texto").value }); };
  $("#p-visual").onsubmit = (ev) => { ev.preventDefault(); const op = { op: "adicionar_visual", tipo: $("#p-tipo").value, medida: $("#p-med").value }; if ($("#p-eixo").value) op.eixo = $("#p-eixo").value; mudar({ op }); };
  $("#p-medida").onsubmit = (ev) => { ev.preventDefault(); mudar({ op: { op: "adicionar_medida", coluna: $("#p-col").value, agregacao: $("#p-agg").value } }); };
  document.querySelectorAll("[data-rem]").forEach((b) => (b.onclick = () => mudar({ op: { op: "remover_visual", id: b.dataset.rem } })));
}

// ---- Conversar com os dados (LST-35) --------------------------------------------------------
const CAMADA2 = { "aguardando revisor": "aguardando revisor", aprovado: "aprovado pelo revisor", reprovado: "reprovado pelo revisor" };

function insightHtml(i) {
  const cols = i.linhas?.[0]?.length || 0;
  return `<div class="insight" style="display:grid;gap:6px;padding:10px 0;border-bottom:1px dashed var(--linha)">
    <p style="margin:0">${esc(i.texto)}</p>
    <details><summary class="quem">ver a consulta e o resultado (conferido pelo auditor)</summary>
      <pre>${esc(i.sql)}</pre>
      <div class="tabela"><table><tbody>${(i.linhas || []).map((l) => `<tr>${l.map((v) => `<td class="${typeof v === "number" ? "n" : ""}">${num(v)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
    </details></div>`;
}

async function telaConversa(did, aviso = "") {
  const alvo = $("#conversa-dem");
  const turnos = await (await api(`/api/demandas/${did}/conversa`)).json();
  const revisa = ["revisor", "admin"].includes(sessao.papel);
  const ultimo = turnos[turnos.length - 1];
  const sugestoes = ultimo?.sugestoes || ["Quanto foi o total?", "Quem lidera?", "Está concentrado em poucos?", "Como evoluiu no último mês?"];
  alvo.innerHTML = `<h2>Conversar com os dados</h2>
    <div class="bloco">
      <p class="quem">Pergunte sobre o resultado aprovado. Cada resposta traz a consulta que a prova: o auditor refaz a conta (camada 1) e o revisor aprova antes de você levar adiante (camada 2). Nada é alterado na fonte.</p>
      ${turnos.map((t) => `<div style="display:grid;gap:4px">
        <p class="rot" style="margin:0">${esc(t.autor.split("@")[0])} perguntou · <span class="status ${t.camada2 === "aprovado" ? "aprovada" : t.camada2 === "reprovado" ? "reprovada" : "em_revisao"}">${esc(CAMADA2[t.camada2] || t.camada2)}</span></p>
        <p style="margin:0"><b>${esc(t.pergunta)}</b></p>
        ${t.conferencia ? `<div class="bloco"><p style="margin:0 0 6px"><b>Por que o número não bate</b> <span class="quem">${esc(t.conferencia.texto)}</span></p><ul>${t.conferencia.motivos.map((m) => `<li>${esc(m)}</li>`).join("")}</ul></div>` : ""}
        ${t.insights.map(insightHtml).join("") || (t.conferencia ? "" : `<p class="quem">Nenhum insight com prova para essa pergunta.</p>`)}
        ${t.recusados?.length ? `<p class="quem">${t.recusados.length} insight(s) recusado(s) pelo auditor por falta de prova.</p>` : ""}
        ${t.revisao ? `<p class="quem">${esc(t.revisao.revisor)}: ${esc(t.revisao.parecer || "(sem parecer)")}</p>` : ""}
        ${revisa && t.camada2 === "aguardando revisor" ? `<div class="linha-btn"><button class="btn ouro" data-rev="${t.n}" data-ok="1">aprovar insights</button><button class="btn sec" data-rev="${t.n}" data-ok="0">reprovar</button></div>` : ""}
      </div>`).join(`<hr style="border:0;border-top:1px solid var(--linha);width:100%">`)}
      <form id="c-perguntar" style="display:grid;gap:8px">
        <label for="c-texto">Sua pergunta<input id="c-texto" type="text" required maxlength="300" placeholder="Ex.: quem lidera em valor vendido por estado?"></label>
        <div class="linha-btn">${sugestoes.map((x) => `<button type="button" class="btn sec" data-sug="${esc(x)}">${esc(x)}</button>`).join("")}</div>
        <div class="linha-btn"><button class="btn" type="submit" id="c-enviar">perguntar</button></div>
      </form>
      <p class="${aviso.startsWith("ok:") ? "ok" : "erro-msg"}" id="c-msg" role="status">${esc(aviso.replace(/^ok:/, ""))}</p>
    </div>`;
  document.querySelectorAll("[data-sug]").forEach((b) => (b.onclick = () => { $("#c-texto").value = b.dataset.sug; $("#c-texto").focus(); }));
  $("#c-perguntar").onsubmit = async (ev) => {
    ev.preventDefault();
    const b = $("#c-enviar"); b.disabled = true; b.textContent = "interpretando e conferindo…";
    try { await api(`/api/demandas/${did}/conversa`, { method: "POST", json: { pergunta: $("#c-texto").value } }); await telaConversa(did); }
    catch (err) { $("#c-msg").textContent = err.message; b.disabled = false; b.textContent = "perguntar"; }
  };
  document.querySelectorAll("[data-rev]").forEach((b) => (b.onclick = async () => {
    try { await api(`/api/demandas/${did}/conversa/${b.dataset.rev}/revisao`, { method: "POST", json: { aprovado: b.dataset.ok === "1", parecer: "" } }); await telaConversa(did, "ok:Revisão registrada no rastro."); }
    catch (err) { $("#c-msg").textContent = err.message; }
  }));
}
