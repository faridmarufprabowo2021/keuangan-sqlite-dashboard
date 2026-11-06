/**
 * VALUTA — Precision Financial Dashboard Client
 * Pure Vanilla JavaScript ES6 (Zero bulky bloatware)
 */

const state = {
  summary: null,
  accounts: [],
  categories: [],
  transactions: [],
  budgets: [],
  savings: [],
  cashflow: [],
  breakdown: [],
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
  theme: new URLSearchParams(location.search).get('theme') || localStorage.getItem('valuta_theme') || 'light'
};

// ---------------- Helpers ----------------
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

  const cashflowEl = document.getElementById('statNetCashflow');
  if (cashflowEl) {
    cashflowEl.textContent = (s.net_cashflow >= 0 ? '+' : '') + formatIDR(s.net_cashflow);
    cashflowEl.className = 'badge-tag ' + (s.net_cashflow >= 0 ? 'badge-income' : 'badge-expense');
  }

  const periodLabel = document.getElementById('periodLabel');
  if (periodLabel) {
    periodLabel.textContent = s.period;
  }
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
      <div class="account-item">
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
  const height = 210;
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
    const barW = Math.min(22, (colWidth - 16) / 2);

    const incH = Math.max(3, (d.income / maxVal) * (chartH - 20));
    const expH = Math.max(3, (d.expense / maxVal) * (chartH - 20));

    const incY = chartH - incH;
    const expY = chartH - expH;

    const incX = x + (colWidth / 2) - barW - 3;
    const expX = x + (colWidth / 2) + 3;

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
          Tidak ditemukan riwayat transaksi yang cocok dengan filter.
        </td>
      </tr>
    `;
    updatePaginationUI();
    return;
  }

  tbody.innerHTML = state.transactions.map(t => {
    const isInc = t.type === 'income';
    const sign = isInc ? '+' : '-';
    const amountClass = isInc ? 'income' : 'expense';
    const badgeType = isInc ? 'badge-income' : 'badge-expense';

    return `
      <tr>
        <td class="mono" style="font-size: 13px; color: var(--ink-muted);">${formatDate(t.date)}</td>
        <td>
          <div style="font-weight: 600;">${t.description}</div>
          ${t.payee_merchant ? `<div class="tx-merchant">${t.payee_merchant}</div>` : ''}
        </td>
        <td>
          <span class="badge-tag ${badgeType}">
            ${t.category_name || 'Umum'}
          </span>
        </td>
        <td>
          <span style="font-size: 13px; color: var(--ink-secondary);">${t.account_name}</span>
        </td>
        <td class="tx-amount ${amountClass} val">
          ${sign}${formatIDR(t.amount)}
        </td>
        <td style="text-align: right;">
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
  const res = await apiGet('/api/analytics/cashflow');
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

  const options = state.accounts.map(a => `<option value="${a.id}">${a.name} (${formatIDR(a.current_balance)})</option>`).join('');

  if (filterAcc) {
    filterAcc.innerHTML = '<option value="">Semua Akun / Dompet</option>' + options;
  }
  if (formAcc) {
    formAcc.innerHTML = options;
  }
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
}

function closeAddTxModal() {
  const modal = document.getElementById('modalAddTx');
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
    await refreshAll();
  } else {
    alert('Gagal menyimpan transaksi: ' + (res.message || 'Terjadi kesalahan'));
  }
}

async function deleteTx(id) {
  if (!confirm('Apakah kamu yakin ingin menghapus catatan transaksi ini?')) return;
  const res = await apiDelete(`/api/transactions/${id}`);
  if (res.success) {
    await refreshAll();
  } else {
    alert('Gagal menghapus: ' + (res.message || 'Error'));
  }
}

function toggleTheme() {
  state.theme = state.theme === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', state.theme);
  localStorage.setItem('valuta_theme', state.theme);
}

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
