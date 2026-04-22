
const api = {
  dashboard: "/api/dashboard",
  users: "/api/users",
  groups: "/api/groups",
  expenses: "/api/expenses",
  seed: "/api/seed",
  reset: "/api/reset",
  settlement: (gid) => `/api/settlement/${gid}`
};

function byId(id){ return document.getElementById(id); }
function money(v){ return Number(v).toLocaleString('pt-BR', { style:'currency', currency:'BRL' }); }

let usuarios = [];
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
  return await res.json();
}

function setScreen(screen){
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.rail-btn').forEach(b => b.classList.remove('active'));
  byId(screen).classList.add('active');
  document.querySelector(`.rail-btn[data-screen="${screen}"]`)?.classList.add('active');

  const titles = {
    inicio: 'Início',
    pessoas: 'Pessoas',
    grupos: 'Grupos',
    despesas: 'Despesas',
    liquidacao: 'Liquidação'
  };
  byId('screenTitle').textContent = titles[screen] || 'Início';
}

function abrirExperiencia(){
  byId('app').classList.remove('hidden');
  byId('app').scrollIntoView({behavior:'smooth', block:'start'});
}

function renderStats(dashboard){
  byId('statUsers').textContent = dashboard.usuarios;
  byId('statGroups').textContent = dashboard.grupos;
  byId('statExpenses').textContent = dashboard.despesas;
  byId('statTotal').textContent = money(dashboard.total);
  byId('landingTotal').textContent = money(dashboard.total);
  byId('summaryInline').textContent = `${dashboard.usuarios} pessoas · ${dashboard.grupos} grupos · ${dashboard.despesas} despesas`;
}

function renderUsuarios(){
  const usersList = byId('usersList');
  const groupMembers = byId('groupMembers');
  if(!usuarios.length){
    usersList.innerHTML = '<div class="item"><p>Nenhuma pessoa cadastrada.</p></div>';
    groupMembers.innerHTML = '<div class="feed-sub">Cadastre pessoas primeiro.</div>';
    return;
  }

  usersList.innerHTML = usuarios.map(u => `
    <div class="item">
      <strong>${u.nome}</strong>
      <p>${u.email}</p>
      <p>Pix: ${u.pix || '-'}</p>
    </div>
  `).join('');

  groupMembers.innerHTML = usuarios.map(u => `
    <label class="checkbox-item">
      <input type="checkbox" value="${u.usuario_id}">
      <span>${u.nome}</span>
    </label>
  `).join('');
}

function renderGrupos(){
  const groupsList = byId('groupsList');
  const dashboardGroups = byId('dashboardGroups');
  const expenseGroup = byId('expenseGroup');
  const settlementGroup = byId('settlementGroup');

  if(!grupos.length){
    groupsList.innerHTML = '<div class="item"><p>Nenhum grupo criado.</p></div>';
    dashboardGroups.innerHTML = '<div class="item"><p>Nenhum grupo criado ainda.</p></div>';
    expenseGroup.innerHTML = '<option value="">Nenhum grupo</option>';
    settlementGroup.innerHTML = '<option value="">Nenhum grupo</option>';
    byId('expensePaidBy').innerHTML = '<option value="">Selecione um grupo</option>';
    byId('expenseParticipants').innerHTML = '<div class="feed-sub">Selecione um grupo.</div>';
    return;
  }

  groupsList.innerHTML = grupos.map(g => `
    <div class="item">
      <strong>${g.nome}</strong>
      <p>${g.membros.map(m => m.nome).join(', ')}</p>
    </div>
  `).join('');

  dashboardGroups.innerHTML = grupos.map(g => {
    const qtd = despesas.filter(d => d.grupo_id === g.grupo_id).length;
    const total = despesas.filter(d => d.grupo_id === g.grupo_id).reduce((s, d) => s + Number(d.valor), 0);
    return `
      <div class="item">
        <strong>${g.nome}</strong>
        <p>${qtd} despesa(s) · ${money(total)}</p>
      </div>
    `;
  }).join('');

  const options = grupos.map(g => `<option value="${g.grupo_id}">${g.nome}</option>`).join('');
  expenseGroup.innerHTML = options;
  settlementGroup.innerHTML = options;
  refreshExpenseMembers();
}

function refreshExpenseMembers(){
  const gid = Number(byId('expenseGroup').value);
  const grupo = grupos.find(g => g.grupo_id === gid);
  const payer = byId('expensePaidBy');
  const participants = byId('expenseParticipants');

  if(!grupo){
    payer.innerHTML = '<option value="">Selecione um grupo</option>';
    participants.innerHTML = '<div class="feed-sub">Selecione um grupo.</div>';
    return;
  }

  payer.innerHTML = grupo.membros.map(m => `<option value="${m.usuario_id}">${m.nome}</option>`).join('');
  participants.innerHTML = grupo.membros.map(m => `
    <label class="checkbox-item">
      <input type="checkbox" value="${m.usuario_id}" checked>
      <span>${m.nome}</span>
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
      <div class="feed-sub">Grupo: ${d.grupo_nome}</div>
      <div class="feed-sub">Pago por: ${d.pago_por_nome}</div>
      <div class="feed-sub">Participantes: ${d.participantes.join(', ')}</div>
    </div>
  `).join('');
}

async function renderLiquidacao(){
  const gid = Number(byId('settlementGroup').value);
  if(!gid){
    byId('balancesList').innerHTML = '<div class="item"><p>Selecione um grupo.</p></div>';
    byId('settlementsList').innerHTML = '<div class="item"><p>Selecione um grupo.</p></div>';
    return;
  }

  const data = await getJSON(api.settlement(gid));

  byId('balancesList').innerHTML = data.saldos.length ? data.saldos.map(s => `
    <div class="item">
      <strong>${s.nome}</strong>
      <p class="${s.saldo > 0 ? 'pos' : s.saldo < 0 ? 'neg' : ''}">${money(s.saldo)}</p>
    </div>
  `).join('') : '<div class="item"><p>Sem saldos.</p></div>';

  byId('settlementsList').innerHTML = data.liquidacao.length ? data.liquidacao.map(l => `
    <div class="item">
      <strong>${l.devedor} → ${l.credor}</strong>
      <p>Transferir ${money(l.valor)}</p>
      <p>Pix: ${l.pix_credor || '-'}</p>
    </div>
  `).join('') : '<div class="item"><p>Nada a liquidar.</p></div>';
}

async function carregarTudo(){
  const dashboard = await getJSON(api.dashboard);
  usuarios = await getJSON(api.users);
  grupos = await getJSON(api.groups);
  despesas = await getJSON(api.expenses);

  renderStats(dashboard);
  renderUsuarios();
  renderGrupos();
  renderDespesas();
  await renderLiquidacao();
}

document.querySelectorAll('.rail-btn').forEach(btn => {
  btn.addEventListener('click', () => setScreen(btn.dataset.screen));
});

byId('seedBtn').addEventListener('click', async () => {
  await postJSON(api.seed, {});
  await carregarTudo();
});

byId('openBtn').addEventListener('click', abrirExperiencia);

byId('resetBtn').addEventListener('click', async () => {
  const ok = confirm('Deseja apagar todos os dados da demonstração?');
  if(!ok) return;
  await postJSON(api.reset, {});
  await carregarTudo();
});

byId('userForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  await postJSON(api.users, {
    nome: byId('userName').value.trim(),
    email: byId('userEmail').value.trim(),
    pix: byId('userPix').value.trim(),
    senha: '123'
  });
  e.target.reset();
  await carregarTudo();
});

byId('groupForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const membros = [...document.querySelectorAll('#groupMembers input:checked')].map(el => Number(el.value));
  if(!membros.length){
    alert('Selecione ao menos uma pessoa.');
    return;
  }
  await postJSON(api.groups, {
    nome: byId('groupName').value.trim(),
    membros
  });
  e.target.reset();
  await carregarTudo();
});

byId('expenseGroup').addEventListener('change', refreshExpenseMembers);

byId('expenseForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const participantes = [...document.querySelectorAll('#expenseParticipants input:checked')].map(el => Number(el.value));
  if(!participantes.length){
    alert('Selecione ao menos um participante.');
    return;
  }
  await postJSON(api.expenses, {
    grupo_id: Number(byId('expenseGroup').value),
    descricao: byId('expenseDescription').value.trim(),
    valor: Number(byId('expenseValue').value),
    pago_por: Number(byId('expensePaidBy').value),
    categoria: byId('expenseCategory').value,
    participantes
  });
  e.target.reset();
  await carregarTudo();
});

byId('refreshSettlementBtn').addEventListener('click', renderLiquidacao);
byId('settlementGroup').addEventListener('change', renderLiquidacao);

carregarTudo();
setScreen('inicio');
