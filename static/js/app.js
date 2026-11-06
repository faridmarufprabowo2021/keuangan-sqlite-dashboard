/**
 * VALUTA — Precision Financial Dashboard Client
 * Pure Vanilla JavaScript ES6 (Zero bulky bloatware)
 * Elevated UI/UX with Sparklines, Slide-Over Receipt Drawer, Quick Chips, & Hotkeys
 */

const state = {
  summary: null,
  accounts: [],
  categories: [],
  transactions: [],
  budgets: [],
  savings: [],
  cashflow: [],
  filters: {
    search: '',
    type: '',
    category_id: '',
    account_id: '',
    page: 1,
    limit: 15
  },
  pagination: {
    total: 0,
    page: 1,
    pages: 1
  },
  activeTx: null,
  theme: new URLSearchParams(location.search).get('theme') || localStorage.getItem('valuta_theme') || 'light'
};

// ---------------- Helpers & Formatters ----------------
function formatIDR(amount) {
  const num = Number(amount) || 0;
  return 'Rp ' + Math.round(num).toLocaleString('id-ID');
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const options = { day: 'numeric', month: 'short', year: 'numeric' };
  return d.toLocaleDateString('id-ID', options);
}

function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <span style="color:var(--accent);">●</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}

// ---------------- API Calls ----------------
async function apiGet(endpoint) {
  try {
    const res = await fetch(endpoint);
    return await res.json();
  } catch (err) {
    console.error('API GET Error:', endpoint, err);
    return null;
  }
}

async function apiPost(endpoint, body) {
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    return await res.json();
  } catch (err) {
    console.error('API POST Error:', endpoint, err);
    return { error: true, message: err.message };
  }
}

async function apiDelete(endpoint) {
  try {
    const res = await fetch(endpoint, { method: 'DELETE' });
    return await res.json();
  } catch (err) {
    console.error('API DELETE Error:', endpoint, err);
    return { error: true, message: err.message };
  }
}

// ---------------- Render Functions ----------------
function renderSummary() {
  const s = state.summary;
  if (!s) return;

  document.getElementById('statNetWorth').textContent = formatIDR(s.total_net_worth);
  document.getElementById('statIncome').textContent = formatIDR(s.month_income);
  document.getElementById('statExpense').textContent = formatIDR(s.month_expense);
  document.getElementById('statSavingsRate').textContent = s.savings_rate + '%';

  const accCountEl = document.getElementById('statAccCount');
  if (accCountEl) accCountEl.textContent = `${s.accounts_count} Akun`;

  const cashflowEl = document.getElementById('statNetCashflow');
  if (cashflowEl) {
    cashflowEl.textContent = (s.net_cashflow >= 0 ? '+' : '') + formatIDR(s.net_cashflow);
    cashflowEl.className = 'badge-tag ' + (s.net_cashflow >= 0 ? 'badge-income' : 'badge-expense');
  }

  const periodLabel = document.getElementById('periodLabel');
  if (periodLabel) periodLabel.textContent = s.period;

  const expTrendEl = document.getElementById('statExpenseTrend');
  if (expTrendEl) {
    const delta = s.expense_growth_vs_last_month;
    if (delta <= 0) {
      expTrendEl.textContent = `↓ Hemat ${Math.abs(delta)}%`;
      expTrendEl.className = 'badge-tag badge-income';
    } else {
      expTrendEl.textContent = `↑ Naik ${delta}%`;
      expTrendEl.className = 'badge-tag badge-expense';
    }
  }

  renderSparklines();
}

function renderSparklines() {
  const cf = state.cashflow;
  if (!cf || cf.length < 2) return;

  function makeSparkline(values, strokeColor, containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const min = Math.min(...values);
    const max = Math.max(...values, min + 1);
    const w = 180;
    const h = 24;
    const pts = values.map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / (max - min)) * (h - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');

    el.innerHTML = `
      <svg viewBox="0 0 ${w} ${h}">
        <polyline fill="none" stroke="${strokeColor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" points="${pts}" />
      </svg>
    `;
  }

  // Net trajectory
  const netVals = cf.map(d => d.income - d.expense);
  makeSparkline(netVals, 'var(--accent)', 'sparklineNetWorth');

  // Income trajectory
  const incVals = cf.map(d => d.income);
  makeSparkline(incVals, 'var(--income)', 'sparklineIncome');

  // Expense trajectory
  const expVals = cf.map(d => d.expense);
  makeSparkline(expVals, 'var(--expense)', 'sparklineExpense');

  // Savings rate
  const savVals = cf.map(d => d.income > 0 ? ((d.income - d.expense) / d.income) * 100 : 0);
  makeSparkline(savVals, 'var(--accent)', 'sparklineSavings');
}

function renderAccounts() {
  const list = document.getElementById('accountsList');
  if (!list) return;

  if (state.accounts.length === 0) {
    list.innerHTML = '<div style="padding:16px;text-align:center;color:var(--ink-muted);">Belum ada akun terdaftar</div>';
    return;
  }

  list.innerHTML = state.accounts.map(acc => {
    const initial = acc.institution.substring(0, 3).toUpperCase();
    return `
      <div class="account-item" onclick="filterByAccount(${acc.id})" title="Klik untuk memfilter transaksi akun ini">
        <div class="account-info">
          <div class="account-icon" style="background-color: ${acc.color};">
            ${initial}
          </div>
          <div>
            <div class="account-name">${acc.name}</div>
            <div class="account-institution">${acc.institution} ${acc.account_number ? '· ' + acc.account_number : ''}</div>
          </div>
        </div>
        <div class="account-balance val">${formatIDR(acc.current_balance)}</div>
      </div>
    `;
  }).join('');
}

function renderCashflowChart() {
  const container = document.getElementById('cashflowChart');
  if (!container) return;

  const data = state.cashflow;
  if (!data || data.length === 0) {
    container.innerHTML = '<div style="text-align:center;padding:60px;color:var(--ink-muted);">Belum cukup data riwayat arus kas</div>';
    return;
  }

  const maxVal = Math.max(...data.map(d => Math.max(d.income, d.expense)), 1000000);
  const width = 640;
  const height = 220;
  const paddingBottom = 28;
  const chartH = height - paddingBottom;
  const colWidth = width / data.length;

  let svgContent = '';

  // Grid lines
  for (let i = 1; i <= 3; i++) {
    const y = Math.round(chartH - (chartH * (i / 4)));
    svgContent += `<line x1="0" y1="${y}" x2="${width}" y2="${y}" stroke="var(--border)" stroke-dasharray="4 4" />`;
  }

  // Bars & Labels
  data.forEach((d, idx) => {
    const x = idx * colWidth;
    const barW = Math.min(22, (colWidth - 18) / 2);

    const incH = Math.max(4, (d.income / maxVal) * (chartH - 20));
    const expH = Math.max(4, (d.expense / maxVal) * (chartH - 20));

    const incY = chartH - incH;
    const expY = chartH - expH;

    const incX = x + (colWidth / 2) - barW - 4;
    const expX = x + (colWidth / 2) + 4;

    // Income Bar
    svgContent += `
      <rect x="${incX}" y="${incY}" width="${barW}" height="${incH}" rx="4" fill="var(--income)" opacity="0.88">
        <title>${d.month} Pemasukan: ${formatIDR(d.income)}</title>
      </rect>
    `;

    // Expense Bar
    svgContent += `
      <rect x="${expX}" y="${expY}" width="${barW}" height="${expH}" rx="4" fill="var(--expense)" opacity="0.88">
        <title>${d.month} Pengeluaran: ${formatIDR(d.expense)}</title>
      </rect>
    `;

    // Month Label
    const monthShort = d.month.split('-')[1];
    const monthNames = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
    const label = monthNames[parseInt(monthShort, 10)] || d.month;

    svgContent += `
      <text x="${x + colWidth / 2}" y="${height - 6}" font-family="var(--font-mono)" font-size="11" fill="var(--ink-muted)" text-anchor="middle">
        ${label}
      </text>
    `;
  });

  container.innerHTML = `
    <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      ${svgContent}
    </svg>
  `;
}

function renderBudgets() {
  const container = document.getElementById('budgetsList');
  if (!container) return;

  if (state.budgets.length === 0) {
    container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--ink-muted);">Belum ada target anggaran bulan ini</div>';
    return;
  }

  container.innerHTML = state.budgets.map(b => {
    const isOver = b.is_exceeded;
    const barColor = isOver ? 'var(--expense)' : (b.percentage > 80 ? 'var(--warning)' : 'var(--accent)');
    const barWidth = Math.min(100, b.percentage);

    return `
      <div class="progress-item">
        <div class="progress-header">
          <span class="progress-name">${b.category_name}</span>
          <span class="progress-stats val">${formatIDR(b.spent)} / ${formatIDR(b.monthly_limit)} (${b.percentage}%)</span>
        </div>
        <div class="progress-track">
          <div class="progress-bar" style="width: ${barWidth}%; background-color: ${barColor};"></div>
        </div>
      </div>
    `;
  }).join('');
}

function renderSavings() {
  const container = document.getElementById('savingsList');
  if (!container) return;

  if (state.savings.length === 0) {
    container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--ink-muted);">Belum ada target tabungan</div>';
    return;
  }

  container.innerHTML = state.savings.map(g => {
    return `
      <div class="progress-item">
        <div class="progress-header">
          <span class="progress-name">${g.title}</span>
          <span class="progress-stats val">${formatIDR(g.current_amount)} / ${formatIDR(g.target_amount)} (${g.percentage}%)</span>
        </div>
        <div class="progress-track">
          <div class="progress-bar" style="width: ${g.percentage}%; background-color: ${g.color};"></div>
        </div>
      </div>
    `;
  }).join('');
}

function renderTransactions() {
  const tbody = document.getElementById('transactionsTableBody');
  if (!tbody) return;

  if (state.transactions.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 48px 16px; color: var(--ink-muted);">
          Tidak ditemukan riwayat transaksi yang cocok dengan filter saat ini.
        </td>
      </tr>
    `;
    updatePaginationUI();
    return;
  }

  tbody.innerHTML = state.transactions.map(t => {
    const isInc = t.type === 'income';
    const isTrf = t.type === 'transfer';
    let sign = '-';
    let amountClass = 'expense';
    let badgeType = 'badge-expense';

    if (isInc) {
      sign = '+';
      amountClass = 'income';
      badgeType = 'badge-income';
    } else if (isTrf) {
      sign = '⇄ ';
      amountClass = 'transfer';
      badgeType = 'badge-transfer';
    }

    return `
      <tr onclick="openTxDrawer(${t.id})">
        <td class="mono" style="font-size: 13px; color: var(--ink-muted);">${formatDate(t.date)}</td>
        <td>
          <div style="font-weight: 600;">${t.description}</div>
          ${t.payee_merchant ? `<div class="tx-merchant">${t.payee_merchant}</div>` : ''}
        </td>
        <td>
          <span class="badge-tag ${badgeType}">
            ${t.category_name || (isTrf ? 'Transfer' : 'Umum')}
          </span>
        </td>
        <td>
          <span style="font-size: 13px; color: var(--ink-secondary);">${t.account_name}</span>
        </td>
        <td class="tx-amount ${amountClass} val">
          ${sign}${formatIDR(t.amount)}
        </td>
        <td style="text-align: right;" onclick="event.stopPropagation()">
          <button class="btn btn-ghost btn-sm" onclick="deleteTx(${t.id})" title="Hapus transaksi">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  updatePaginationUI();
}

function updatePaginationUI() {
  const meta = state.pagination;
  const countEl = document.getElementById('txTotalCount');
  const pageIndicator = document.getElementById('txPageIndicator');
  const prevBtn = document.getElementById('btnPrevPage');
  const nextBtn = document.getElementById('btnNextPage');

  if (countEl) countEl.textContent = `Menampilkan ${state.transactions.length} dari ${meta.total} transaksi`;
  if (pageIndicator) pageIndicator.textContent = `Hal ${meta.page} dari ${meta.pages}`;

  if (prevBtn) prevBtn.disabled = meta.page <= 1;
  if (nextBtn) nextBtn.disabled = meta.page >= meta.pages;
}

// ---------------- Slide-Over Transaction Drawer ----------------
function openTxDrawer(txId) {
  const tx = state.transactions.find(t => t.id === txId);
  if (!tx) return;
  state.activeTx = tx;

  const drawer = document.getElementById('drawerTxDetail');
  const isInc = tx.type === 'income';
  const isTrf = tx.type === 'transfer';

  document.getElementById('drawerId').textContent = `#TX-${tx.id.toString().padStart(5, '0')}`;
  document.getElementById('drawerAmount').textContent = (isInc ? '+' : (isTrf ? '⇄ ' : '-')) + formatIDR(tx.amount);
  document.getElementById('drawerAmount').style.color = isInc ? 'var(--income)' : (isTrf ? 'var(--transfer)' : 'var(--expense)');
  document.getElementById('drawerDesc').textContent = tx.description;
  document.getElementById('drawerDate').textContent = formatDate(tx.date) + ` (${tx.date})`;
  document.getElementById('drawerCat').textContent = tx.category_name || (isTrf ? 'Transfer Antar Rekening' : 'Umum');
  document.getElementById('drawerAcc').textContent = tx.account_name + (tx.to_account_name ? ` → ${tx.to_account_name}` : '');
  document.getElementById('drawerMerchant').textContent = tx.payee_merchant || '-';

  const badgeEl = document.getElementById('drawerBadge');
  badgeEl.textContent = tx.type.toUpperCase();
  badgeEl.className = 'badge-tag ' + (isInc ? 'badge-income' : (isTrf ? 'badge-transfer' : 'badge-expense'));

  const notesRow = document.getElementById('drawerNotesRow');
  const notesEl = document.getElementById('drawerNotes');
  if (tx.notes) {
    notesRow.style.display = 'flex';
    notesEl.textContent = tx.notes;
  } else {
    notesRow.style.display = 'none';
  }

  const deleteBtn = document.getElementById('btnDrawerDelete');
  deleteBtn.onclick = () => {
    deleteTx(tx.id);
    closeTxDrawer();
  };

  drawer.classList.add('active');
}

function closeTxDrawer(e) {
  if (e && e.target !== e.currentTarget && !e.target.closest('.drawer-header button') && !e.target.closest('.drawer-footer button')) return;
  const drawer = document.getElementById('drawerTxDetail');
  drawer.classList.remove('active');
  state.activeTx = null;
}

// ---------------- Quick Filters & Nav Switcher ----------------
function switchNavTab(tabName, el) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  if (el) el.classList.add('active');

  const targets = {
    overview: 'sectionOverview',
    ledger: 'sectionLedger',
    budgets: 'sectionBudgets',
    accounts: 'sectionAccounts'
  };

  const id = targets[tabName];
  if (id) {
    const targetEl = document.getElementById(id);
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}

function applyQuickFilter(type, el) {
  document.querySelectorAll('.quick-chip').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');

  state.filters.type = type;
  state.filters.category_id = '';
  state.filters.page = 1;

  const typeSelect = document.getElementById('filterType');
  if (typeSelect) typeSelect.value = type;

  const catSelect = document.getElementById('filterCategory');
  if (catSelect) catSelect.value = '';

  loadTransactions();
}

function applyQuickCategory(catName, el) {
  document.querySelectorAll('.quick-chip').forEach(c => c.classList.remove('active'));
  if (el) el.classList.add('active');

  const cat = state.categories.find(c => c.name === catName);
  state.filters.category_id = cat ? cat.id : '';
  state.filters.type = '';
  state.filters.page = 1;

  const catSelect = document.getElementById('filterCategory');
  if (catSelect && cat) catSelect.value = cat.id;

  const typeSelect = document.getElementById('filterType');
  if (typeSelect) typeSelect.value = '';

  loadTransactions();
}

function filterByAccount(accId) {
  const accSelect = document.getElementById('filterAccount');
  if (accSelect) accSelect.value = accId;
  state.filters.account_id = accId;
  state.filters.page = 1;
  loadTransactions();
  const ledgerEl = document.getElementById('sectionLedger');
  if (ledgerEl) ledgerEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  showToast(`Memfilter transaksi akun ID #${accId}`);
}

// ---------------- Data Refresh ----------------
async function loadSummary() {
  const res = await apiGet('/api/summary');
  state.summary = res ? res.data : null;
  renderSummary();
}

async function loadAccounts() {
  const res = await apiGet('/api/accounts');
  state.accounts = (res && res.data) ? res.data : [];
  renderAccounts();
  populateAccountSelects();
}

async function loadCategories() {
  const res = await apiGet('/api/categories');
  state.categories = (res && res.data) ? res.data : [];
  populateCategorySelects();
}

async function loadBudgets() {
  const res = await apiGet('/api/budgets');
  state.budgets = (res && res.data) ? res.data : [];
  renderBudgets();
}

async function loadSavings() {
  const res = await apiGet('/api/savings');
  state.savings = (res && res.data) ? res.data : [];
  renderSavings();
}

async function loadCashflow() {
  const res = await apiGet('/api/analytics/cashflow?months=6');
  state.cashflow = (res && res.data) ? res.data : [];
  renderCashflowChart();
}

async function loadTransactions() {
  const f = state.filters;
  const qs = new URLSearchParams({
    search: f.search,
    type: f.type,
    category_id: f.category_id,
    account_id: f.account_id,
    page: f.page,
    limit: f.limit
  });
  const res = await apiGet(`/api/transactions?${qs.toString()}`);
  if (res && res.data) {
    state.transactions = res.data;
    state.pagination = res.meta || { total: res.data.length, page: 1, pages: 1 };
  } else {
    state.transactions = [];
    state.pagination = { total: 0, page: 1, pages: 1 };
  }
  renderTransactions();
}

function populateAccountSelects() {
  const filterAcc = document.getElementById('filterAccount');
  const formAcc = document.getElementById('txAccount');
  const trFrom = document.getElementById('trFromAcc');
  const trTo = document.getElementById('trToAcc');

  const options = state.accounts.map(a => `<option value="${a.id}">${a.name} (${formatIDR(a.current_balance)})</option>`).join('');

  if (filterAcc) filterAcc.innerHTML = '<option value="">Semua Akun / Dompet</option>' + options;
  if (formAcc) formAcc.innerHTML = options;
  if (trFrom) trFrom.innerHTML = options;
  if (trTo) trTo.innerHTML = options;
}

function populateCategorySelects() {
  const filterCat = document.getElementById('filterCategory');
  const formCat = document.getElementById('txCategory');
  const formType = document.getElementById('txType');
  const selectedType = formType ? formType.value : 'expense';

  if (filterCat) {
    const allOptions = state.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    filterCat.innerHTML = '<option value="">Semua Kategori</option>' + allOptions;
  }

  if (formCat) {
    const filtered = state.categories.filter(c => c.type === selectedType);
    formCat.innerHTML = filtered.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
  }
}

async function refreshAll() {
  await Promise.all([
    loadSummary(),
    loadAccounts(),
    loadCategories(),
    loadBudgets(),
    loadSavings(),
    loadCashflow(),
    loadTransactions()
  ]);
}

// ---------------- Actions & Modals ----------------
function openAddTxModal() {
  const modal = document.getElementById('modalAddTx');
  const dateInput = document.getElementById('txDate');
  if (dateInput && !dateInput.value) {
    dateInput.value = new Date().toISOString().split('T')[0];
  }
  populateCategorySelects();
  modal.classList.add('active');
  setTimeout(() => document.getElementById('txAmount')?.focus(), 100);
}

function closeAddTxModal() {
  const modal = document.getElementById('modalAddTx');
  modal.classList.remove('active');
}

function openTransferModal() {
  const modal = document.getElementById('modalTransfer');
  const dateInput = document.getElementById('trDate');
  if (dateInput && !dateInput.value) {
    dateInput.value = new Date().toISOString().split('T')[0];
  }
  populateAccountSelects();
  modal.classList.add('active');
  setTimeout(() => document.getElementById('trAmount')?.focus(), 100);
}

function closeTransferModal() {
  const modal = document.getElementById('modalTransfer');
  modal.classList.remove('active');
}

async function saveTransaction(e) {
  e.preventDefault();
  const accId = document.getElementById('txAccount').value;
  const catId = document.getElementById('txCategory').value;
  const type = document.getElementById('txType').value;
  const amount = document.getElementById('txAmount').value;
  const date = document.getElementById('txDate').value;
  const desc = document.getElementById('txDesc').value;
  const merchant = document.getElementById('txMerchant').value;
  const notes = document.getElementById('txNotes').value;

  if (!amount || !desc || !date) {
    alert('Mohon lengkapi nominal, tanggal, dan deskripsi transaksi.');
    return;
  }

  const res = await apiPost('/api/transactions', {
    account_id: parseInt(accId, 10),
    category_id: parseInt(catId, 10),
    type: type,
    amount: parseFloat(amount),
    date: date,
    description: desc,
    payee_merchant: merchant,
    notes: notes
  });

  if (res.success) {
    closeAddTxModal();
    document.getElementById('formAddTx').reset();
    showToast(`Transaksi "${desc}" berhasil disimpan!`);
    await refreshAll();
  } else {
    alert('Gagal menyimpan transaksi: ' + (res.message || 'Terjadi kesalahan'));
  }
}

async function saveTransfer(e) {
  e.preventDefault();
  const fromId = document.getElementById('trFromAcc').value;
  const toId = document.getElementById('trToAcc').value;
  const amount = document.getElementById('trAmount').value;
  const date = document.getElementById('trDate').value;
  const notes = document.getElementById('trNotes').value;

  if (fromId === toId) {
    alert('Akun pengirim dan tujuan tidak boleh sama.');
    return;
  }

  const res = await apiPost('/api/transfer', {
    from_account_id: parseInt(fromId, 10),
    to_account_id: parseInt(toId, 10),
    amount: parseFloat(amount),
    date: date,
    notes: notes
  });

  if (res.success) {
    closeTransferModal();
    document.getElementById('formTransfer').reset();
    showToast(`Transfer dana ${formatIDR(amount)} berhasil diproses!`);
    await refreshAll();
  } else {
    alert('Gagal memproses transfer: ' + (res.message || 'Error'));
  }
}

async function deleteTx(id) {
  if (!confirm('Apakah kamu yakin ingin menghapus catatan transaksi ini?')) return;
  const res = await apiDelete(`/api/transactions/${id}`);
  if (res.success) {
    showToast('Transaksi berhasil dihapus');
    await refreshAll();
  } else {
    alert('Gagal menghapus: ' + (res.message || 'Error'));
  }
}

async function seedDatabase() {
  if (!confirm('Reset ulang data contoh (6 bulan riwayat finansial)?')) return;
  const res = await apiPost('/api/seed', {});
  if (res.success) {
    showToast('Database berhasil di-reset dengan 6 bulan data realistis!');
    await refreshAll();
  }
}

function toggleTheme() {
  state.theme = state.theme === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', state.theme);
  localStorage.setItem('valuta_theme', state.theme);
  showToast(`Tema diubah ke ${state.theme === 'dark' ? 'Dark Mode' : 'Light Mode'}`);
}

// ---------------- Global Keyboard Shortcuts ----------------
window.addEventListener('keydown', (e) => {
  const isInput = ['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName);

  if (e.key === 'Escape') {
    closeAddTxModal();
    closeTransferModal();
    closeTxDrawer();
    return;
  }

  if (isInput) return;

  if (e.key === 'n' || e.key === 'N' || e.key === 'c' || e.key === 'C') {
    e.preventDefault();
    openAddTxModal();
  } else if (e.key === '/') {
    e.preventDefault();
    document.getElementById('txSearch')?.focus();
  } else if (e.key === 't' || e.key === 'T') {
    e.preventDefault();
    toggleTheme();
  }
});

// ---------------- Initialization ----------------
document.addEventListener('DOMContentLoaded', () => {
  // Apply theme
  document.documentElement.setAttribute('data-theme', state.theme);

  // Search input with debounce
  const searchInput = document.getElementById('txSearch');
  if (searchInput) {
    searchInput.addEventListener('input', debounce((e) => {
      state.filters.search = e.target.value.trim();
      state.filters.page = 1;
      loadTransactions();
    }, 250));
  }

  // Filter selects
  const filterType = document.getElementById('filterType');
  if (filterType) {
    filterType.addEventListener('change', (e) => {
      state.filters.type = e.target.value;
      state.filters.page = 1;
      loadTransactions();
    });
  }

  const filterCat = document.getElementById('filterCategory');
  if (filterCat) {
    filterCat.addEventListener('change', (e) => {
      state.filters.category_id = e.target.value;
      state.filters.page = 1;
      loadTransactions();
    });
  }

  const filterAcc = document.getElementById('filterAccount');
  if (filterAcc) {
    filterAcc.addEventListener('change', (e) => {
      state.filters.account_id = e.target.value;
      state.filters.page = 1;
      loadTransactions();
    });
  }

  // Type change in modal to filter categories
  const formType = document.getElementById('txType');
  if (formType) {
    formType.addEventListener('change', () => {
      populateCategorySelects();
    });
  }

  // Pagination buttons
  const prevBtn = document.getElementById('btnPrevPage');
  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (state.filters.page > 1) {
        state.filters.page--;
        loadTransactions();
      }
    });
  }

  const nextBtn = document.getElementById('btnNextPage');
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (state.filters.page < state.pagination.pages) {
        state.filters.page++;
        loadTransactions();
      }
    });
  }

  // Initial load
  refreshAll();
});
