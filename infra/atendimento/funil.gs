/**
 * Funil de atendimento do Lastro (card LST-24). Cole na planilha "Lastro · Leads"
 * (Extensões > Apps Script), preencha LINK_AGENDA e rode `configurar` uma vez.
 *
 * O que `configurar` faz: cria o formulário curto, liga as respostas a esta planilha
 * e instala o gatilho que, a cada lead, marca o status "novo", avisa a equipe e
 * responde ao lead com o link de agendamento (reunião no Meet).
 * Nada aqui guarda senha ou token: o script roda com a conta Google de quem autoriza.
 */

const EQUIPE = 'lixumlabs@gmail.com';
const WHATSAPP = '5561999520802';
// Página de agendamento da Agenda (Agenda > Criar > Página de agendamento > Compartilhar).
const LINK_AGENDA = '';

const PERGUNTAS = [
  { titulo: 'Seu nome', tipo: 'texto', obrigatoria: true },
  { titulo: 'E-mail', tipo: 'email', obrigatoria: true },
  { titulo: 'WhatsApp', tipo: 'texto', obrigatoria: false },
  { titulo: 'Empresa', tipo: 'texto', obrigatoria: true },
  { titulo: 'Qual sistema a empresa usa?', tipo: 'texto', obrigatoria: false, ajuda: 'ERP, CRM ou planilha. Ex.: Sienge, Omie, Google Planilhas.' },
  { titulo: 'Qual número mais pesa nas suas decisões hoje?', tipo: 'paragrafo', obrigatoria: true },
];

// ---------- Lógica pura (testada fora do Google em tests/funil.test.js) ----------

function lerLead(respostas) {
  const pega = (t) => String(respostas[t] || '').trim();
  return {
    nome: pega('Seu nome'),
    email: pega('E-mail').toLowerCase(),
    whatsapp: pega('WhatsApp').replace(/\D/g, ''),
    empresa: pega('Empresa'),
    sistema: pega('Qual sistema a empresa usa?') || 'não informado',
    pergunta: pega('Qual número mais pesa nas suas decisões hoje?'),
  };
}

function avisoEquipe(lead, linkPlanilha) {
  const zap = lead.whatsapp ? `https://wa.me/${lead.whatsapp}` : 'não informado';
  return {
    assunto: `Lead novo no Lastro: ${lead.empresa}`,
    corpo: [
      `${lead.nome} (${lead.empresa}) pediu para testar o Lastro.`,
      '',
      `Pergunta: ${lead.pergunta}`,
      `Sistema: ${lead.sistema}`,
      `E-mail: ${lead.email}`,
      `WhatsApp: ${zap}`,
      '',
      `Planilha de leads: ${linkPlanilha}`,
    ].join('\n'),
  };
}

function respostaLead(lead, linkAgenda) {
  const primeiro = lead.nome.split(/\s+/)[0] || lead.nome;
  const marcar = linkAgenda
    ? `Escolha um horário de 30 minutos aqui (a conversa é pelo Google Meet): ${linkAgenda}`
    : `Vamos te chamar para marcar uma conversa de 30 minutos.`;
  return {
    assunto: 'Recebemos a sua pergunta · Lastro',
    corpo: [
      `Olá, ${primeiro}.`,
      '',
      `Recebemos a sua pergunta: "${lead.pergunta}".`,
      marcar,
      '',
      `Se preferir, fale com a gente no WhatsApp: https://wa.me/${WHATSAPP}`,
      '',
      'Equipe Lastro · lixum.labs',
    ].join('\n'),
  };
}

// ---------- Google (só roda no Apps Script) ----------

function configurar() {
  const planilha = SpreadsheetApp.getActiveSpreadsheet();
  const form = FormApp.create('Lastro · testar com os meus dados');
  form.setDescription('Conte a pergunta que mais pesa no seu negócio. Respondemos em até 1 dia útil.');
  form.setCollectEmail(false);
  form.setConfirmationMessage('Recebemos. Mandamos agora um e-mail com o link para marcar a conversa.');
  PERGUNTAS.forEach((p) => {
    const item = p.tipo === 'paragrafo' ? form.addParagraphTextItem() : form.addTextItem();
    item.setTitle(p.titulo).setRequired(p.obrigatoria);
    if (p.ajuda) item.setHelpText(p.ajuda);
    if (p.tipo === 'email') item.setValidation(FormApp.createTextValidation().requireTextIsEmail().build());
  });
  form.setDestination(FormApp.DestinationType.SPREADSHEET, planilha.getId());
  ScriptApp.getProjectTriggers().forEach((t) => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('aoReceberLead').forSpreadsheet(planilha).onFormSubmit().create();
  PropertiesService.getScriptProperties().setProperty('FORM_URL', form.getPublishedUrl());
  Logger.log('Formulário: ' + form.getPublishedUrl());
  Logger.log('Cole este link no botão "deixar a pergunta" do site (LST-24).');
}

function aoReceberLead(e) {
  const aba = e.range.getSheet();
  const cabecalho = aba.getRange(1, 1, 1, aba.getLastColumn()).getValues()[0];
  let colStatus = cabecalho.indexOf('status') + 1;
  if (!colStatus) {
    colStatus = cabecalho.length + 1;
    aba.getRange(1, colStatus).setValue('status');
  }
  aba.getRange(e.range.getRow(), colStatus).setValue('novo');

  const respostas = {};
  Object.keys(e.namedValues).forEach((k) => (respostas[k] = e.namedValues[k][0]));
  const lead = lerLead(respostas);
  const aviso = avisoEquipe(lead, aba.getParent().getUrl());
  MailApp.sendEmail(EQUIPE, aviso.assunto, aviso.corpo, { replyTo: lead.email });
  if (lead.email) {
    const r = respostaLead(lead, LINK_AGENDA);
    MailApp.sendEmail(lead.email, r.assunto, r.corpo, { name: 'Lastro', replyTo: EQUIPE });
  }
}

if (typeof module !== 'undefined') module.exports = { lerLead, avisoEquipe, respostaLead, PERGUNTAS };
