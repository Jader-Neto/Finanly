const api = {
  me: "/api/auth/me",
  login: "/api/auth/login",
  register: "/api/auth/register",
  logout: "/api/auth/logout",
  dashboard: "/api/dashboard",
  contacts: "/api/contacts",
  addContact: "/api/contacts/add",
  groups: "/api/groups",
  expenses: "/api/expenses",
  seed: "/api/seed",
  settlement: (gid) => `/api/settlement/${gid}`
};

function byId(id){ return document.getElementById(id); }
function money(v){ return Number(v).toLocaleString('pt-BR', { style:'currency', currency:'BRL' }); }

let usuarioAtual = null;
let contatos = [];
let grupos = [];
let despesas = [];

async function getJSON(url){
  const res = await fetch(url);
  return await res.json();
}

async function postJSON(url, body){
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body || {})
  });
  const data = await res.json();
  if(!res.ok) alert(data.erro || "Erro na operação.");
  return { ok: res.ok, data };
}

async function showAuth(){
  byId("authPage").classList.remove("hidden");
  byId("appPage").classList.add("hidden");
}

async function showApp(){
  byId("authPage").classList.add("hidden");
  byId("appPage").classList.remove("hidden");
}

async function checkSession(){
  const data = await getJSON(api.me);
  if(data.logado){
    usuarioAtual = data.usuario;
    byId("usuarioLogado").textContent = usuarioAtual.nome;
    byId("publicKey").textContent = usuarioAtual.chave_publica;
    await showApp();
    await carregarTudo();
  }else{
    showAuth();
  }
}

function setScreen(screen){
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.rail-btn').forEach(b => b.classList.remove('active'));
  byId(screen).classList.add('active');
  document.querySelector(`.rail-btn[data-screen="${screen}"]`)?.classList.add('active');
  const titles = {inicio:'Início', contatos:'Contatos', grupos:'Eventos', despesas:'Despesas', liquidacao:'Liquidação'};
  byId('screenTitle').textContent = titles[screen] || 'Início';
}

function renderStats(d){
  byId('statUsers').textContent = d.usuarios;
  byId('statGroups').textContent = d.grupos;
  byId('statExpenses').textContent = d.despesas;
  byId('statTotal').textContent = money(d.total);
  byId('summaryInline').textContent = `${d.usuarios} pessoas · ${d.grupos} eventos · ${d.despesas} despesas`;
}

function renderContatos(){
  const list = byId('contactsList');
  const members = byId('groupMembers');

  if(!contatos.length){
    list.innerHTML = '<div class="item"><p>Nenhum contato ainda.</p></div>';
    members.innerHTML = '<div class="feed-sub">Adicione contatos por chave primeiro.</div>';
    return;
  }

  list.innerHTML = contatos.map(c => `
    <div class="item">
      <strong>${c.nome}${c.usuario_id === usuarioAtual.usuario_id ? ' (você)' : ''}</strong>
      <p>${c.email}</p>
      <p>Pix: ${c.pix || '-'}</p>
      <p>Chave: ${c.chave_publica}</p>
    </div>
  `).join('');

  members.innerHTML = contatos.map(c => `
    <label class="checkbox-item">
      <input type="checkbox" value="${c.usuario_id}" ${c.usuario_id === usuarioAtual.usuario_id ? 'checked disabled' : ''}>
      <span>${c.nome}<br><small>${c.pix || 'Sem Pix'}</small></span>
    </label>
  `).join('');
}

function renderGrupos(){
  const groupsList = byId('groupsList');
  const dash = byId('dashboardGroups');
  const expenseGroup = byId('expenseGroup');
  const settlementGroup = byId('settlementGroup');
  const expenseSubmit = document.querySelector('#expenseForm button[type="submit"]');

  if(!grupos.length){
    groupsList.innerHTML = '<div class="item"><p>Nenhum evento criado.</p></div>';
    dash.innerHTML = '<div class="item"><p>Nenhum evento criado ainda. Crie um evento antes de registrar uma despesa.</p></div>';
    expenseGroup.innerHTML = '<option value="">Crie um evento primeiro</option>';
    settlementGroup.innerHTML = '<option value="">Crie um evento primeiro</option>';
    byId('expensePaidBy').innerHTML = '<option value="">Selecione um evento</option>';
    byId('expenseParticipants').innerHTML = '<div class="feed-sub">Crie ou selecione um evento para escolher participantes.</div>';
    if(expenseSubmit) expenseSubmit.disabled = true;
    return;
  }

  if(expenseSubmit) expenseSubmit.disabled = false;

  groupsList.innerHTML = grupos.map(g => `
    <div class="item">
      <strong>${g.nome}</strong>
      <p>${g.membros.map(m => m.nome).join(', ')}</p>
      <p>Criado em: ${g.criado_em}</p>
    </div>
  `).join('');

  dash.innerHTML = grupos.map(g => {
    const qtd = despesas.filter(d => d.grupo_id === g.grupo_id).length;
    const total = despesas.filter(d => d.grupo_id === g.grupo_id).reduce((sum, d) => sum + Number(d.valor), 0);
    return `<div class="item"><strong>${g.nome}</strong><p>${qtd} despesa(s) · ${money(total)}</p></div>`;
  }).join('');

  const opts = grupos.map(g => `<option value="${g.grupo_id}">${g.nome}</option>`).join('');
  expenseGroup.innerHTML = opts;
  settlementGroup.innerHTML = opts;
  refreshExpenseMembers();
}

function refreshExpenseMembers(){
  const gid = Number(byId('expenseGroup').value);
  const group = grupos.find(g => g.grupo_id === gid);
  const payer = byId('expensePaidBy');
  const participants = byId('expenseParticipants');

  if(!group){
    payer.innerHTML = '<option value="">Selecione um evento</option>';
    participants.innerHTML = '<div class="feed-sub">Selecione um evento.</div>';
    return;
  }

  payer.innerHTML = group.membros.map(m => `<option value="${m.usuario_id}">${m.nome}</option>`).join('');
  participants.innerHTML = group.membros.map(m => `
    <label class="checkbox-item">
      <input type="checkbox" value="${m.usuario_id}" checked>
      <span>${m.nome}<br><small>${m.pix || 'Sem Pix'}</small></span>
    </label>
  `).join('');
}

function renderDespesas(){
  const box = byId('expensesList');
  if(!despesas.length){
    box.innerHTML = '<div class="item"><p>Nenhuma despesa registrada.</p></div>';
    return;
  }

  box.innerHTML = [...despesas].reverse().map(d => `
    <div class="feed-card">
      <div class="feed-title">${d.descricao}</div>
      <div class="feed-sub">${money(d.valor)} · <span class="tag">${d.categoria}</span></div>
      <div class="feed-sub">Evento: ${d.grupo_nome}</div>
      <div class="feed-sub">Cobrado por: ${d.pago_por_nome}</div>
      <div class="feed-sub">Participantes: ${d.participantes.join(', ')}</div>
      ${d.anexo_url ? `<img class="attachment" src="${d.anexo_url}">` : ''}
      ${d.pago_por_pix ? `<div class="item top-gap"><strong>Pix do cobrador</strong><p>${d.pago_por_pix}</p><p>${d.pix_link}</p></div>` : ''}
      <button class="btn btn-outline top-gap" onclick="removerDespesa(${d.despesa_id})">Remover despesa</button>
    </div>
  `).join('');
}

async function renderLiquidacao(){
  const gid = Number(byId('settlementGroup').value);
  if(!gid){
    byId('balancesList').innerHTML = '<div class="item"><p>Selecione um evento.</p></div>';
    byId('settlementsList').innerHTML = '<div class="item"><p>Selecione um evento.</p></div>';
    return;
  }

  const data = await getJSON(api.settlement(gid));
  byId('balancesList').innerHTML = data.saldos.length ? data.saldos.map(s => `
    <div class="item"><strong>${s.nome}</strong><p class="${s.saldo > 0 ? 'pos' : s.saldo < 0 ? 'neg' : ''}">${money(s.saldo)}</p></div>
  `).join('') : '<div class="item"><p>Sem saldos.</p></div>';

  byId('settlementsList').innerHTML = data.liquidacao.length ? data.liquidacao.map(l => `
    <div class="item"><strong>${l.devedor} → ${l.credor}</strong><p>Transferir ${money(l.valor)}</p><p>Pix: ${l.pix_credor || '-'}</p></div>
  `).join('') : '<div class="item"><p>Nada a liquidar.</p></div>';
}

async function carregarTudo(){
  const dashboard = await getJSON(api.dashboard);
  contatos = await getJSON(api.contacts);
  grupos = await getJSON(api.groups);
  despesas = await getJSON(api.expenses);

  renderStats(dashboard);
  renderContatos();
  renderGrupos();
  renderDespesas();
  await renderLiquidacao();
}

async function removerDespesa(id){
  if(confirm('Remover esta despesa?')){
    await fetch(`/api/expenses/${id}`, { method:'DELETE' });
    await carregarTudo();
  }
}

document.querySelectorAll('.auth-tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.auth-tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    btn.classList.add('active');
    byId(btn.dataset.auth + 'Form').classList.add('active');
  });
});

byId('loginForm').addEventListener('submit', async e => {
  e.preventDefault();
  const r = await postJSON(api.login, { email: byId('loginEmail').value, senha: byId('loginSenha').value });
  if(r.ok) await checkSession();
});

byId('registerForm').addEventListener('submit', async e => {
  e.preventDefault();
  const r = await postJSON(api.register, {
    nome: byId('registerNome').value,
    email: byId('registerEmail').value,
    senha: byId('registerSenha').value,
    pix: byId('registerPix').value
  });
  if(r.ok) await checkSession();
});

byId('logoutBtn').addEventListener('click', async () => {
  await postJSON(api.logout, {});
  usuarioAtual = null;
  showAuth();
});

byId('copyKeyBtn').addEventListener('click', async () => {
  await navigator.clipboard.writeText(usuarioAtual.chave_publica);
  alert('Chave copiada!');
});

byId('contactForm').addEventListener('submit', async e => {
  e.preventDefault();
  const r = await postJSON(api.addContact, { chave: byId('contactKey').value });
  if(r.ok){
    e.target.reset();
    await carregarTudo();
  }
});

document.querySelectorAll('.rail-btn').forEach(btn => btn.addEventListener('click', () => setScreen(btn.dataset.screen)));

byId('seedBtn').addEventListener('click', async () => {
  await postJSON(api.seed, {});
  await carregarTudo();
});

byId('groupForm').addEventListener('submit', async e => {
  e.preventDefault();
  const membros = [...document.querySelectorAll('#groupMembers input:checked')].map(el => Number(el.value));
  const r = await postJSON(api.groups, { nome: byId('groupName').value.trim(), membros });
  if(r.ok){
    e.target.reset();
    await carregarTudo();
  }
});

byId('expenseGroup').addEventListener('change', refreshExpenseMembers);

byId('expenseForm').addEventListener('submit', async e => {
  e.preventDefault();

  if(!grupos.length){
    alert('Crie um evento antes de registrar uma despesa.');
    return;
  }

  const participantes = [...document.querySelectorAll('#expenseParticipants input:checked')].map(el => Number(el.value));
  if(!participantes.length){
    alert('Selecione pelo menos um participante.');
    return;
  }

  const form = new FormData();
  form.append('grupo_id', byId('expenseGroup').value);
  form.append('descricao', byId('expenseDescription').value.trim());
  form.append('valor', byId('expenseValue').value);
  form.append('pago_por', byId('expensePaidBy').value);
  form.append('categoria', byId('expenseCategory').value);
  participantes.forEach(p => form.append('participantes', p));
  const img = byId('expenseImage').files[0];
  if(img) form.append('imagem', img);

  const res = await fetch(api.expenses, { method:'POST', body: form });
  const data = await res.json();
  if(!res.ok){
    alert(data.erro || 'Erro ao registrar despesa.');
    return;
  }

  e.target.reset();
  await carregarTudo();
  setScreen('despesas');
});

byId('refreshSettlementBtn').addEventListener('click', renderLiquidacao);
byId('settlementGroup').addEventListener('change', renderLiquidacao);

checkSession();
setScreen('inicio');
