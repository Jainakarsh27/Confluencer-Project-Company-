// =====================================================================
// LEDGERFLOW CLIENT KERNEL — MULTI-VIEW SPA, 2FA AUTH & TREASURY ENGINE
// =====================================================================

const API_BASE = '/api/v1';

const state = {
  activeView: 'landing', // 'landing', 'auth', 'dashboard'
  currentUser: {
    name: 'Akarsh Jain',
    role: 'Lead Full Stack Architect',
    avatar: '/static/akarsh_jain.jpg',
    isEvaluator: false
  },
  accounts: [],
  currentAccountId: null,
  currentAccountName: '',
  currentBalance: '0.00',
  currentTypeFilter: '',
  currentPage: 1,
  currentLimit: 10,
  totalPages: 1,
  totalRecords: 0,
  searchTerm: '',
  allLoadedItems: []
};

// =====================================================================
// DOM ELEMENT HOOKS
// =====================================================================

// Views
const viewLanding = document.getElementById('viewLanding');
const viewAuth = document.getElementById('viewAuth');
const viewDashboard = document.getElementById('viewDashboard');

// Landing Page CTAs
const btnNavSignIn = document.getElementById('btnNavSignIn');
const btnQuickDemoPass = document.getElementById('btnQuickDemoPass');
const btnHeroEnterPortal = document.getElementById('btnHeroEnterPortal');
const btnQuickLoginAkarsh = document.getElementById('btnQuickLoginAkarsh');

// Auth View Controls
const btnAuthBackToLanding = document.getElementById('btnAuthBackToLanding');
const authTabs = document.querySelectorAll('.auth-tab');
const authTabPanels = document.querySelectorAll('.auth-tab-panel');
const btnTriggerBiometric = document.getElementById('btnTriggerBiometric');
const scanStatusTitle = document.getElementById('scanStatusTitle');
const scanStatusSub = document.getElementById('scanStatusSub');
const btnLoginRecruiter = document.getElementById('btnLoginRecruiter');
const formRegisterNewAccount = document.getElementById('formRegisterNewAccount');
const regAccountName = document.getElementById('regAccountName');
const totpCodeValue = document.getElementById('totpCodeValue');
const totpTimerBadge = document.getElementById('totpTimerBadge');
const btnCopyTotp = document.getElementById('btnCopyTotp');
const inputTotpVerification = document.getElementById('inputTotpVerification');

// Dashboard Topbar & Sidebar
const btnTopLandingIntro = document.getElementById('btnTopLandingIntro');
const btnLockSession = document.getElementById('btnLockSession');
const accountSelect = document.getElementById('accountSelect');
const btnNewAccountModal = document.getElementById('btnNewAccountModal');
const btnResetSlate = document.getElementById('btnResetSlate');
const btnTopRefresh = document.getElementById('btnTopRefresh');
const searchInput = document.getElementById('searchInput');

// Treasury Display
const heroAccountName = document.getElementById('heroAccountName');
const heroAccountId = document.getElementById('heroAccountId');
const heroAccountDate = document.getElementById('heroAccountDate');
const heroBalance = document.getElementById('heroBalance');
const cardHolderName = document.getElementById('cardHolderName');
const cardAccountId = document.getElementById('cardAccountId');
const btnCopyAccountId = document.getElementById('btnCopyAccountId');
const kpiCredits = document.getElementById('kpiCredits');
const kpiDebits = document.getElementById('kpiDebits');
const kpiCount = document.getElementById('kpiCount');
const journalCountBadge = document.getElementById('journalCountBadge');

// Actions & Stress Lab
const btnOpenCreditModal = document.getElementById('btnOpenCreditModal');
const btnOpenDebitModal = document.getElementById('btnOpenDebitModal');
const btnOpenAuditModal = document.getElementById('btnOpenAuditModal');
const btnSimulateOverdraft = document.getElementById('btnSimulateOverdraft');
const btnSimulateDuplicate = document.getElementById('btnSimulateDuplicate');
const btnSimulateConcurrency = document.getElementById('btnSimulateConcurrency');
const telemetryFeed = document.getElementById('telemetryFeed');

// Journal Table & Pagination
const transactionTableBody = document.getElementById('transactionTableBody');
const pagStart = document.getElementById('pagStart');
const pagEnd = document.getElementById('pagEnd');
const pagTotalRecords = document.getElementById('pagTotalRecords');
const pagCurrentPage = document.getElementById('pagCurrentPage');
const pagTotalPages = document.getElementById('pagTotalPages');
const btnPrevPage = document.getElementById('btnPrevPage');
const btnNextPage = document.getElementById('btnNextPage');
const pageSizeSelect = document.getElementById('pageSizeSelect');

// Modals
const modalCreateAccount = document.getElementById('modalCreateAccount');
const formCreateAccount = document.getElementById('formCreateAccount');
const inputAccountName = document.getElementById('inputAccountName');

const modalTransaction = document.getElementById('modalTransaction');
const formTransaction = document.getElementById('formTransaction');
const txModalEyebrow = document.getElementById('txModalEyebrow');
const txModalTitle = document.getElementById('txModalTitle');
const txType = document.getElementById('txType');
const txAmount = document.getElementById('txAmount');
const txDescription = document.getElementById('txDescription');
const txReference = document.getElementById('txReference');
const btnGenReference = document.getElementById('btnGenReference');

const modalAudit = document.getElementById('modalAudit');
const auditLoading = document.getElementById('auditLoading');
const auditContent = document.getElementById('auditContent');
const auditStoredBalance = document.getElementById('auditStoredBalance');
const auditCalcBalance = document.getElementById('auditCalcBalance');
const auditCredits = document.getElementById('auditCredits');
const auditDebits = document.getElementById('auditDebits');
const auditTxCount = document.getElementById('auditTxCount');
const btnRecheckAudit = document.getElementById('btnRecheckAudit');

// =====================================================================
// UTILITIES: TOASTS & TELEMETRY
// =====================================================================

function showToast(title, body, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast-item ${type}`;
  toast.innerHTML = `
    <div>
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-body">${escapeHtml(body)}</div>
    </div>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

function logTelemetry(msg, type = 'info') {
  if (!telemetryFeed) return;
  const now = new Date();
  const timeStr = now.toTimeString().split(' ')[0] + '.' + String(now.getMilliseconds()).padStart(3, '0');
  const line = document.createElement('div');
  line.className = `telemetry-line ${type}`;
  line.innerHTML = `
    <span class="time">[${timeStr}]</span>
    <span class="msg">${escapeHtml(msg)}</span>
  `;
  telemetryFeed.appendChild(line);
  telemetryFeed.scrollTop = telemetryFeed.scrollHeight;
}

function generateRef(prefix = 'REF') {
  const rand = Math.random().toString(36).substring(2, 7).toUpperCase();
  const num = Math.floor(1000 + Math.random() * 9000);
  return `${prefix}-${num}-${rand}`;
}

function formatDate(isoStr) {
  if (!isoStr) return '---';
  const d = new Date(isoStr);
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
}

function formatCurrency(val) {
  const num = parseFloat(val || 0);
  return num.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// =====================================================================
// VIEW ROUTER
// =====================================================================

function switchView(viewName) {
  state.activeView = viewName;
  [viewLanding, viewAuth, viewDashboard].forEach(v => {
    if (v) v.classList.remove('active');
  });

  if (viewName === 'landing') {
    if (viewLanding) viewLanding.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else if (viewName === 'auth') {
    if (viewAuth) viewAuth.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else if (viewName === 'dashboard') {
    if (viewDashboard) viewDashboard.classList.add('active');
    loadAccounts();
  }
}

// =====================================================================
// AUTHENTICATION & 2FA CONTROLLER
// =====================================================================

let currentTotpCode = '849 201';
let totpRemainingSec = 30;
let totpInterval = null;

function startTotpCountdown() {
  if (totpInterval) clearInterval(totpInterval);
  totpRemainingSec = 30;
  generateNewTotp();

  totpInterval = setInterval(() => {
    totpRemainingSec--;
    if (totpRemainingSec <= 0) {
      totpRemainingSec = 30;
      generateNewTotp();
    }
    if (totpTimerBadge) {
      totpTimerBadge.textContent = `REFRESH IN ${totpRemainingSec}s`;
    }
  }, 1000);
}

function generateNewTotp() {
  const p1 = Math.floor(100 + Math.random() * 900);
  const p2 = Math.floor(100 + Math.random() * 900);
  currentTotpCode = `${p1} ${p2}`;
  if (totpCodeValue) totpCodeValue.textContent = currentTotpCode;
}

// Auth Tab Switching
authTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    authTabs.forEach(t => t.classList.remove('active'));
    authTabPanels.forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    const targetPanel = document.getElementById(tab.dataset.tab);
    if (targetPanel) targetPanel.classList.add('active');
  });
});

// Biometric Passkey Simulation (Akarsh Jain)
if (btnTriggerBiometric) {
  btnTriggerBiometric.addEventListener('click', () => {
    if (scanStatusTitle && scanStatusSub) {
      scanStatusTitle.textContent = "Scanning Biometric Touch ID...";
      scanStatusSub.textContent = "Verifying cryptographic hardware token...";
      btnTriggerBiometric.disabled = true;
      btnTriggerBiometric.innerHTML = `<span class="pulse-dot"></span> Authenticating Operator Signature...`;

      setTimeout(() => {
        scanStatusTitle.textContent = "Cryptographic Signature Verified";
        scanStatusSub.textContent = "Access Level: ROOT_TREASURY_ADMIN granted.";
        showToast("Biometric Handshake Success", "Identity confirmed: Akarsh Jain (Lead Full Stack Architect)", "success");

        state.currentUser = {
          name: 'Akarsh Jain',
          role: 'Lead Full Stack Architect',
          avatar: '/static/akarsh_jain.jpg',
          isEvaluator: false
        };

        setTimeout(() => {
          btnTriggerBiometric.disabled = false;
          btnTriggerBiometric.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Authenticate with Passkey &amp; Open Console`;
          switchView('dashboard');
        }, 600);
      }, 900);
    }
  });
}

// Recruiter Evaluator Sandbox Access
if (btnLoginRecruiter) {
  btnLoginRecruiter.addEventListener('click', () => {
    showToast("Sandbox Access Granted", "Entering Treasury Core with Recruiter Evaluator clearance.", "info");
    state.currentUser = {
      name: 'Recruiter Evaluator',
      role: 'Technical Reviewer',
      avatar: '/static/akarsh_jain.jpg',
      isEvaluator: true
    };
    switchView('dashboard');
  });
}

// Register New Account with 2FA TOTP
if (btnCopyTotp) {
  btnCopyTotp.addEventListener('click', () => {
    if (inputTotpVerification) {
      inputTotpVerification.value = currentTotpCode;
      showToast("TOTP Code Copied", `Filled ${currentTotpCode} into verification input.`, "info");
    }
  });
}

if (formRegisterNewAccount) {
  formRegisterNewAccount.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = regAccountName.value.trim();
    if (!name) return;

    try {
      const res = await fetch(`${API_BASE}/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });

      if (!res.ok) {
        const err = await res.json();
        showToast("Account Creation Rejected", err.error?.message || "Failed to establish account", "error");
        return;
      }

      const newAcc = await res.json();
      showToast("Account Established", `Welcome, ${newAcc.name}! Initial balance strictly verified at ₹0.00.`, "success");
      formRegisterNewAccount.reset();
      switchView('dashboard');
    } catch (err) {
      showToast("Network Error", err.message, "error");
    }
  });
}

// Navigation CTA Listeners
if (btnNavSignIn) btnNavSignIn.addEventListener('click', () => switchView('auth'));
if (btnQuickDemoPass) {
  btnQuickDemoPass.addEventListener('click', () => {
    showToast("Recruiter Pass Active", "Bypassing to Treasury Console for instant invariant evaluation.", "info");
    switchView('dashboard');
  });
}
if (btnHeroEnterPortal) btnHeroEnterPortal.addEventListener('click', () => switchView('auth'));
if (btnQuickLoginAkarsh) {
  btnQuickLoginAkarsh.addEventListener('click', () => {
    switchView('auth');
    // Select Akarsh tab
    const akarshTab = document.querySelector('[data-tab="tab-akarsh"]');
    if (akarshTab) akarshTab.click();
  });
}
if (btnAuthBackToLanding) btnAuthBackToLanding.addEventListener('click', () => switchView('landing'));
if (btnTopLandingIntro) btnTopLandingIntro.addEventListener('click', () => switchView('landing'));
if (btnLockSession) {
  btnLockSession.addEventListener('click', () => {
    showToast("Session Locked", "Operator signed out. Treasury locks engaged.", "warn");
    switchView('auth');
  });
}

// =====================================================================
// DATA LAYER & TREASURY ENGINE LOGIC
// =====================================================================

async function loadAccounts() {
  try {
    const res = await fetch(`${API_BASE}/accounts?limit=100`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const accounts = await res.json();
    state.accounts = accounts;

    accountSelect.innerHTML = '';
    if (accounts.length === 0) {
      accountSelect.innerHTML = '<option value="">-- No Accounts (Create New) --</option>';
      setEmptyAccountState();
      return;
    }

    accounts.forEach(acc => {
      const opt = document.createElement('option');
      opt.value = acc.id;
      opt.textContent = `${acc.name} (₹${formatCurrency(acc.balance)})`;
      accountSelect.appendChild(opt);
    });

    // Keep active or select first
    const targetId = state.currentAccountId && accounts.some(a => a.id === state.currentAccountId)
      ? state.currentAccountId
      : accounts[0].id;

    accountSelect.value = targetId;
    selectAccount(targetId);
  } catch (err) {
    showToast("Ledger Sync Failure", `Unable to fetch accounts: ${err.message}`, "error");
    logTelemetry(`Failed to query accounts: ${err.message}`, 'reject');
  }
}

function setEmptyAccountState() {
  state.currentAccountId = null;
  state.currentAccountName = 'No Accounts Found';
  heroAccountName.textContent = 'No Accounts Found';
  heroAccountId.textContent = 'Click "Open New Account" to begin';
  heroAccountDate.textContent = '---';
  heroBalance.textContent = '0.00';
  cardHolderName.textContent = 'RECRUITER / EVALUATOR';
  cardAccountId.textContent = '•••• •••• •••• ••••';
  kpiCredits.textContent = '+₹0.00';
  kpiDebits.textContent = '-₹0.00';
  kpiCount.textContent = '0';
  journalCountBadge.textContent = '0 Entries';
  transactionTableBody.innerHTML = `<tr><td colspan="6" class="table-empty-state">No accounts exist in database. Establish one to test transactions.</td></tr>`;
}

function selectAccount(accountId) {
  const acc = state.accounts.find(a => a.id === accountId);
  if (!acc) return;

  state.currentAccountId = acc.id;
  state.currentAccountName = acc.name;
  state.currentBalance = acc.balance;
  state.currentPage = 1;

  heroAccountName.textContent = acc.name;
  heroAccountId.textContent = acc.id;
  heroAccountDate.textContent = formatDate(acc.created_at);
  heroBalance.textContent = formatCurrency(acc.balance);

  cardHolderName.textContent = acc.name;
  cardAccountId.textContent = `${acc.id.substring(0, 4)} •••• •••• ${acc.id.substring(acc.id.length - 4)}`;

  logTelemetry(`Active account context switched to: ${acc.name} [${acc.id}]`, 'info');
  loadTransactions();
  syncLiveBalance();
}

async function syncLiveBalance() {
  if (!state.currentAccountId) return;
  try {
    const res = await fetch(`${API_BASE}/accounts/${state.currentAccountId}/balance`);
    if (res.ok) {
      const data = await res.json();
      state.currentBalance = data.balance;
      heroBalance.textContent = formatCurrency(data.balance);
    }
  } catch (err) {
    console.error("Balance sync failed", err);
  }
}

async function loadTransactions() {
  if (!state.currentAccountId) return;

  const typeParam = state.currentTypeFilter ? `&type=${state.currentTypeFilter}` : '';
  const url = `${API_BASE}/transactions?account_id=${state.currentAccountId}&page=${state.currentPage}&limit=${state.currentLimit}${typeParam}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.totalRecords = data.total;
    state.totalPages = data.pages || 1;
    state.allLoadedItems = data.items;

    renderJournalTable(data.items);
    updatePaginationUI(data);
    updateKPIs(data.items, data.total);
  } catch (err) {
    showToast("Journal Sync Error", err.message, "error");
    transactionTableBody.innerHTML = `<tr><td colspan="6" class="table-empty-state">Error querying transaction ledger.</td></tr>`;
  }
}

function renderJournalTable(items) {
  const term = state.searchTerm.toLowerCase();
  const filtered = term
    ? items.filter(tx => 
        tx.description.toLowerCase().includes(term) ||
        tx.reference_id.toLowerCase().includes(term) ||
        tx.id.toLowerCase().includes(term)
      )
    : items;

  journalCountBadge.textContent = `${state.totalRecords} Entries`;

  if (filtered.length === 0) {
    transactionTableBody.innerHTML = `<tr><td colspan="6" class="table-empty-state">No transaction records found matching active filter.</td></tr>`;
    return;
  }

  transactionTableBody.innerHTML = filtered.map(tx => {
    const isCredit = tx.type.toLowerCase() === 'credit';
    const tagClass = isCredit ? 'tag-emerald' : 'tag-rose';
    const sign = isCredit ? '+' : '-';
    const amountClass = isCredit ? 'text-emerald' : 'text-rose';

    return `
      <tr>
        <td><span class="tag ${tagClass}">${tx.type.toUpperCase()}</span></td>
        <td class="font-mono ${amountClass}" style="font-weight: 700;">${sign}₹${formatCurrency(tx.amount)}</td>
        <td style="color: #ffffff; font-weight: 500;">${escapeHtml(tx.description)}</td>
        <td><code class="font-mono text-amber" style="font-size: 0.8rem;">${escapeHtml(tx.reference_id)}</code></td>
        <td class="font-mono" style="font-size: 0.78rem;">${formatDate(tx.created_at)}</td>
        <td><code class="font-mono" style="font-size: 0.72rem; color: var(--text-faint);">${tx.id.substring(0, 8)}...</code></td>
      </tr>
    `;
  }).join('');
}

function updatePaginationUI(data) {
  const start = data.total === 0 ? 0 : (data.page - 1) * data.limit + 1;
  const end = Math.min(data.page * data.limit, data.total);

  pagStart.textContent = start;
  pagEnd.textContent = end;
  pagTotalRecords.textContent = data.total;
  pagCurrentPage.textContent = data.page;
  pagTotalPages.textContent = data.pages || 1;

  btnPrevPage.disabled = data.page <= 1;
  btnNextPage.disabled = data.page >= data.pages;
}

function updateKPIs(items, totalCount) {
  let credits = 0;
  let debits = 0;
  items.forEach(tx => {
    const amt = parseFloat(tx.amount || 0);
    if (tx.type.toLowerCase() === 'credit') credits += amt;
    else debits += amt;
  });

  kpiCredits.textContent = `+₹${formatCurrency(credits)}`;
  kpiDebits.textContent = `-₹${formatCurrency(debits)}`;
  kpiCount.textContent = totalCount;
}

// =====================================================================
// TRANSACTION POSTING (CREDIT / DEBIT)
// =====================================================================

function openTxModal(type) {
  if (!state.currentAccountId) {
    showToast("No Account Selected", "Please select or create an account first.", "warn");
    return;
  }
  txType.value = type;
  const isCredit = type === 'credit';
  txModalEyebrow.textContent = isCredit ? 'INWARD LIQUIDITY' : 'DISBURSEMENT UNIT';
  txModalTitle.textContent = isCredit ? 'Deposit Funds (Credit)' : 'Disburse Funds (Debit)';
  txAmount.value = '';
  txDescription.value = isCredit ? 'Treasury Capital Influx' : 'Operating Vendor Payment';
  txReference.value = generateRef(isCredit ? 'DEP' : 'DIS');
  modalTransaction.classList.remove('hidden');
  txAmount.focus();
}

if (btnOpenCreditModal) btnOpenCreditModal.addEventListener('click', () => openTxModal('credit'));
if (btnOpenDebitModal) btnOpenDebitModal.addEventListener('click', () => openTxModal('debit'));
if (btnGenReference) btnGenReference.addEventListener('click', () => {
  txReference.value = generateRef(txType.value === 'credit' ? 'DEP' : 'DIS');
});

// Quick Amount Chips
document.querySelectorAll('.quick-chips .chip').forEach(btn => {
  btn.addEventListener('click', () => {
    txAmount.value = btn.dataset.amount;
  });
});

if (formTransaction) {
  formTransaction.addEventListener('submit', async (e) => {
    e.preventDefault();
    const type = txType.value;
    const amount = txAmount.value.trim();
    const description = txDescription.value.trim();
    const reference_id = txReference.value.trim();

    if (!amount || !description || !reference_id) return;

    try {
      const res = await fetch(`${API_BASE}/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: state.currentAccountId,
          type,
          amount: parseFloat(amount),
          description,
          reference_id
        })
      });

      const resData = await res.json();

      if (res.status === 201) {
        modalTransaction.classList.add('hidden');
        showToast("Transaction Posted", `Successfully executed ${type.toUpperCase()} for ₹${formatCurrency(amount)}.`, "success");
        logTelemetry(`[SUCCESS] ${type.toUpperCase()} ₹${amount} posted. Ref: ${reference_id}`, type);
        await syncLiveBalance();
        await loadTransactions();
      } else if (res.status === 409) {
        showToast("Idempotency Replay Caught", `Reference ${reference_id} already exists on this account. Rejected with HTTP 409.`, "warn");
        logTelemetry(`[IDEMPOTENCY CONFLICT 409] Duplicate reference ${reference_id} blocked.`, 'reject');
      } else if (res.status === 422) {
        showToast("Solvency Deficit", resData.error?.message || "Insufficient funds for debit operation.", "error");
        logTelemetry(`[OVERDRAFT REJECT 422] ${resData.error?.message || 'Insufficient funds'}`, 'reject');
      } else {
        showToast("Transaction Error", resData.error?.message || "Failed to process transaction", "error");
        logTelemetry(`[ERROR ${res.status}] ${resData.error?.message || 'Unknown error'}`, 'reject');
      }
    } catch (err) {
      showToast("Network Failure", err.message, "error");
      logTelemetry(`[NETWORK FAILURE] ${err.message}`, 'reject');
    }
  });
}

// =====================================================================
// MATHEMATICAL AUDIT RECONCILIATION VAULT
// =====================================================================

async function runReconciliation() {
  if (!state.currentAccountId) return;
  modalAudit.classList.remove('hidden');
  auditLoading.classList.remove('hidden');
  auditContent.classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE}/accounts/${state.currentAccountId}/reconciliation`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    auditLoading.classList.add('hidden');
    auditContent.classList.remove('hidden');

    auditStoredBalance.textContent = `₹${formatCurrency(data.stored_balance)}`;
    auditCalcBalance.textContent = `₹${formatCurrency(data.calculated_balance)}`;
    auditCredits.textContent = `+₹${formatCurrency(data.total_credits)}`;
    auditDebits.textContent = `-₹${formatCurrency(data.total_debits)}`;
    auditTxCount.textContent = data.transaction_count;

    logTelemetry(`[AUDIT VAULT] Reconciliation completed for ${state.currentAccountName}. Consistent=${data.is_consistent}`, 'info');
  } catch (err) {
    showToast("Audit Failed", err.message, "error");
    modalAudit.classList.add('hidden');
  }
}

if (btnOpenAuditModal) btnOpenAuditModal.addEventListener('click', runReconciliation);
if (btnRecheckAudit) btnRecheckAudit.addEventListener('click', runReconciliation);

// =====================================================================
// CHAOS STRESS LAB SIMULATORS
// =====================================================================

// 1. Overdraft Rejection Test
if (btnSimulateOverdraft) {
  btnSimulateOverdraft.addEventListener('click', async () => {
    if (!state.currentAccountId) return;
    logTelemetry(`[CHAOS SIM] Triggering Overdraft Rejection Test (debiting ₹99,999.00)...`, 'reject');
    try {
      const res = await fetch(`${API_BASE}/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: state.currentAccountId,
          type: 'debit',
          amount: 99999.00,
          description: 'Simulated Chaos Overdraft Attack',
          reference_id: generateRef('CHAOS-OVD')
        })
      });
      const data = await res.json();
      if (res.status === 422) {
        showToast("Invariant Verified: 422 Caught", "Backend correctly rejected overdraft. Balance remained unaltered.", "success");
        logTelemetry(`[CHAOS PASS] Invariant upheld. 422 Unprocessable Entity returned: "${data.error?.message}"`, 'system');
      } else {
        showToast("Unexpected Result", `Received HTTP ${res.status}`, "warn");
      }
    } catch (err) {
      showToast("Chaos Test Failed", err.message, "error");
    }
  });
}

// 2. Duplicate Idempotency Replay Test
if (btnSimulateDuplicate) {
  btnSimulateDuplicate.addEventListener('click', async () => {
    if (!state.currentAccountId) return;
    const testRef = generateRef('CHAOS-DUP');
    logTelemetry(`[CHAOS SIM] Step 1: Submitting initial credit with ref ${testRef}...`, 'info');

    try {
      // First submission
      const res1 = await fetch(`${API_BASE}/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: state.currentAccountId,
          type: 'credit',
          amount: 25.00,
          description: 'Idempotency Baseline Deposit',
          reference_id: testRef
        })
      });

      if (res1.status === 201) {
        logTelemetry(`[CHAOS SIM] Step 2: Replaying EXACT SAME reference ${testRef}...`, 'reject');
        // Immediate duplicate submission
        const res2 = await fetch(`${API_BASE}/transactions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            account_id: state.currentAccountId,
            type: 'credit',
            amount: 25.00,
            description: 'Duplicate Replay Attempt',
            reference_id: testRef
          })
        });

        if (res2.status === 409) {
          showToast("Idempotency Invariant Verified", "Second attempt blocked with HTTP 409 Conflict. Zero double-spending occurred.", "success");
          logTelemetry(`[CHAOS PASS] Unique constraint (account_id, reference_id) enforced 409 Conflict!`, 'system');
          await syncLiveBalance();
          await loadTransactions();
        } else {
          showToast("Warning", `Duplicate returned HTTP ${res2.status}`, "warn");
        }
      }
    } catch (err) {
      showToast("Duplicate Test Failed", err.message, "error");
    }
  });
}

// 3. 5x Parallel Microsecond Race Test
if (btnSimulateConcurrency) {
  btnSimulateConcurrency.addEventListener('click', async () => {
    if (!state.currentAccountId) return;
    logTelemetry(`[CONCURRENCY RACE] Seeding account with ₹100.00 liquidity...`, 'info');

    // Deposit seed
    await fetch(`${API_BASE}/transactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account_id: state.currentAccountId,
        type: 'credit',
        amount: 100.00,
        description: 'Concurrency Test Seed Capital',
        reference_id: generateRef('SEED')
      })
    });

    logTelemetry(`[CONCURRENCY RACE] Firing 5 simultaneous parallel debits of ₹60.00 each...`, 'reject');

    const promises = [1, 2, 3, 4, 5].map(i => 
      fetch(`${API_BASE}/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: state.currentAccountId,
          type: 'debit',
          amount: 60.00,
          description: `Parallel Debit Worker #${i}`,
          reference_id: generateRef(`RACE-${i}`)
        })
      }).then(r => r.json().then(data => ({ status: r.status, data })))
    );

    const results = await Promise.all(promises);
    const successCount = results.filter(r => r.status === 201).length;
    const rejectCount = results.filter(r => r.status === 422).length;

    logTelemetry(`[RACE RESULTS] ${successCount} Debits Committed, ${rejectCount} Deficits Rejected with 422.`, 'system');
    showToast("Concurrency Race Concluded", `${successCount} debit approved, ${rejectCount} overspends blocked by SELECT FOR UPDATE locks.`, "success");

    await syncLiveBalance();
    await loadTransactions();
  });
}

// =====================================================================
// SLATE RESET & CONTROLS
// =====================================================================

if (btnResetSlate) {
  btnResetSlate.addEventListener('click', async () => {
    if (!confirm("Are you sure you want to reset all accounts and transactions to a clean slate? This allows recruiters to evaluate from a 100% fresh start.")) {
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/accounts/system/reset`, { method: 'POST' });
      if (res.ok) {
        showToast("Database Reset Complete", "All test accounts and transactions cleared. Fresh state active.", "info");
        logTelemetry("[DATABASE SLATE WIPED] System returned to clean test state.", 'system');
        await loadAccounts();
      }
    } catch (err) {
      showToast("Reset Failed", err.message, "error");
    }
  });
}

if (btnTopRefresh) {
  btnTopRefresh.addEventListener('click', async () => {
    showToast("Synchronizing", "Fetching latest ledger state from backend...", "info");
    await syncLiveBalance();
    await loadTransactions();
  });
}

if (accountSelect) {
  accountSelect.addEventListener('change', (e) => {
    if (e.target.value) {
      selectAccount(e.target.value);
    }
  });
}

if (btnCopyAccountId) {
  btnCopyAccountId.addEventListener('click', () => {
    if (state.currentAccountId) {
      navigator.clipboard.writeText(state.currentAccountId);
      showToast("Copied to Clipboard", state.currentAccountId, "info");
    }
  });
}

// Search Filter Input
if (searchInput) {
  searchInput.addEventListener('input', (e) => {
    state.searchTerm = e.target.value;
    renderJournalTable(state.allLoadedItems);
  });

  window.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== searchInput) {
      e.preventDefault();
      searchInput.focus();
    }
  });
}

// Segmented Filter
document.querySelectorAll('.segment-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.currentTypeFilter = btn.dataset.type;
    state.currentPage = 1;
    loadTransactions();
  });
});

// Page Size Select
if (pageSizeSelect) {
  pageSizeSelect.addEventListener('change', (e) => {
    state.currentLimit = parseInt(e.target.value, 10);
    state.currentPage = 1;
    loadTransactions();
  });
}

// Pagination Nav
if (btnPrevPage) {
  btnPrevPage.addEventListener('click', () => {
    if (state.currentPage > 1) {
      state.currentPage--;
      loadTransactions();
    }
  });
}

if (btnNextPage) {
  btnNextPage.addEventListener('click', () => {
    if (state.currentPage < state.totalPages) {
      state.currentPage++;
      loadTransactions();
    }
  });
}

// Create Account Modal
if (btnNewAccountModal) {
  btnNewAccountModal.addEventListener('click', () => {
    inputAccountName.value = '';
    modalCreateAccount.classList.remove('hidden');
    inputAccountName.focus();
  });
}

if (formCreateAccount) {
  formCreateAccount.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = inputAccountName.value.trim();
    if (!name) return;

    try {
      const res = await fetch(`${API_BASE}/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });

      if (!res.ok) {
        const err = await res.json();
        showToast("Validation Error", err.error?.message || "Failed to create account", "error");
        return;
      }

      const acc = await res.json();
      modalCreateAccount.classList.add('hidden');
      showToast("Account Created", `Established ${acc.name} with initial balance strictly ₹0.00`, "success");
      logTelemetry(`[ACCOUNT CREATED] ${acc.name} (${acc.id}) initialized with 0.00 balance.`, 'info');

      state.currentAccountId = acc.id;
      await loadAccounts();
    } catch (err) {
      showToast("Creation Error", err.message, "error");
    }
  });
}

// Generic Close Modal buttons
document.querySelectorAll('[data-close]').forEach(btn => {
  btn.addEventListener('click', () => {
    const modalId = btn.getAttribute('data-close');
    const targetModal = document.getElementById(modalId);
    if (targetModal) targetModal.classList.add('hidden');
  });
});

// Close modals on scrim click
document.querySelectorAll('.modal-scrim').forEach(scrim => {
  scrim.addEventListener('click', (e) => {
    if (e.target === scrim) scrim.classList.add('hidden');
  });
});

// =====================================================================
// INITIALIZATION
// =====================================================================

window.addEventListener('DOMContentLoaded', () => {
  startTotpCountdown();
  // Start on landing view to provide authentic product intro showcase
  switchView('landing');
});
