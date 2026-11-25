// Teste da lógica do funil com um lead fictício (node infra/atendimento/funil.test.js).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const mod = { exports: {} };
new Function('module', fs.readFileSync(path.join(__dirname, 'funil.gs'), 'utf8'))(mod);
const { lerLead, avisoEquipe, respostaLead, PERGUNTAS } = mod.exports;

const respostas = {
  'Seu nome': '  Marina Teixeira ',
  'E-mail': 'Marina@Construtora-Exemplo.com.br',
  WhatsApp: '(61) 98888-7777',
  Empresa: 'Construtora Exemplo',
  'Qual sistema a empresa usa?': '',
  'Qual número mais pesa nas suas decisões hoje?': 'Margem por obra no mês',
};
for (const p of PERGUNTAS) assert.ok(p.titulo in respostas, `pergunta sem resposta no teste: ${p.titulo}`);

const lead = lerLead(respostas);
assert.equal(lead.nome, 'Marina Teixeira');
assert.equal(lead.email, 'marina@construtora-exemplo.com.br');
assert.equal(lead.whatsapp, '61988887777');
assert.equal(lead.sistema, 'não informado');

const aviso = avisoEquipe(lead, 'https://docs.google.com/spreadsheets/d/x');
assert.match(aviso.assunto, /Construtora Exemplo/);
assert.match(aviso.corpo, /Margem por obra no mês/);
assert.match(aviso.corpo, /wa\.me\/61988887777/);

const comAgenda = respostaLead(lead, 'https://calendar.app.google/abc');
assert.match(comAgenda.corpo, /^Olá, Marina\./);
assert.match(comAgenda.corpo, /calendar\.app\.google\/abc/);
assert.match(comAgenda.corpo, /Google Meet/);
const semAgenda = respostaLead(lead, '');
assert.doesNotMatch(semAgenda.corpo, /undefined|calendar/);

console.log('funil: 11 checagens ok com lead fictício');
