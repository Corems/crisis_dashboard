<template>
  <div class="stock-analyzer">
    <h2 class="section-title">📊 Фундаментальний аналіз акції</h2>

    <!-- Search -->
    <div class="search-row">
      <input
        v-model="ticker"
        class="ticker-input"
        placeholder="Введи тікер: AAPL, MSFT, NVDA..."
        maxlength="10"
        @keyup.enter="analyze"
        @input="ticker = ticker.toUpperCase()"
      />
      <button class="analyze-btn" :disabled="loading || !ticker.trim()" @click="analyze">
        <span v-if="loading" class="spinner" />
        <span v-else>Аналізувати</span>
      </button>
      <button v-if="data" class="refresh-btn" :disabled="loading" @click="analyze(true)" title="Оновити (ігнорувати кеш)">
        ↻
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-box">
      ⚠️ {{ error }}
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="skeleton-wrap">
      <div class="skeleton" style="height:80px" />
      <div class="skeleton" style="height:220px; margin-top:12px" />
      <div class="skeleton" style="height:160px; margin-top:12px" />
    </div>

    <!-- Results -->
    <template v-if="data && !loading">
      <!-- Header -->
      <div class="company-header">
        <div class="company-info">
          <span class="ticker-badge">{{ data.ticker }}</span>
          <span class="company-name">{{ data.company_name }}</span>
        </div>
        <div class="company-meta">
          <span class="badge">{{ data.sector }}</span>
          <span class="badge muted">{{ data.industry }}</span>
          <span v-if="data.market_cap" class="badge green">
            Mcap {{ formatBillions(data.market_cap) }}
          </span>
          <span v-if="data.cached" class="badge muted">🗄 кеш 24h</span>
        </div>
      </div>

      <!-- Metrics grid -->
      <div class="metrics-grid">
        <!-- Valuation -->
        <div class="metrics-card">
          <h3>📐 Оцінка</h3>
          <table class="metrics-table">
            <tbody>
              <tr><td>P/E (trailing)</td><td>{{ fmt(data.pe_trailing, 'x') }}</td></tr>
              <tr><td>P/E (forward)</td><td>{{ fmt(data.pe_forward, 'x') }}</td></tr>
              <tr><td>P/B</td><td>{{ fmt(data.pb, 'x') }}</td></tr>
              <tr><td>P/S</td><td>{{ fmt(data.ps, 'x') }}</td></tr>
              <tr><td>EV/EBITDA</td><td>{{ fmt(data.ev_ebitda, 'x') }}</td></tr>
              <tr><td>PEG</td><td>{{ fmt(data.peg, 'x') }}</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Profitability -->
        <div class="metrics-card">
          <h3>💰 Прибутковість</h3>
          <table class="metrics-table">
            <tbody>
              <tr><td>Чиста маржа</td><td :class="pctClass(data.profit_margin)">{{ fmt(data.profit_margin, '%') }}</td></tr>
              <tr><td>Операційна маржа</td><td :class="pctClass(data.oper_margin)">{{ fmt(data.oper_margin, '%') }}</td></tr>
              <tr><td>Валова маржа</td><td :class="pctClass(data.gross_margin)">{{ fmt(data.gross_margin, '%') }}</td></tr>
              <tr><td>ROE</td><td :class="pctClass(data.roe)">{{ fmt(data.roe, '%') }}</td></tr>
              <tr><td>ROA</td><td :class="pctClass(data.roa)">{{ fmt(data.roa, '%') }}</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Growth -->
        <div class="metrics-card">
          <h3>📈 Зростання (YoY)</h3>
          <table class="metrics-table">
            <tbody>
              <tr><td>Виручка</td><td :class="pctClass(data.rev_growth)">{{ fmt(data.rev_growth, '%') }}</td></tr>
              <tr><td>Прибуток</td><td :class="pctClass(data.earn_growth)">{{ fmt(data.earn_growth, '%') }}</td></tr>
              <tr><td>Виручка (квартал)</td><td :class="pctClass(data.rev_qtr_growth)">{{ fmt(data.rev_qtr_growth, '%') }}</td></tr>
            </tbody>
          </table>

          <h3 style="margin-top:16px">🏦 Фінансове здоров'я</h3>
          <table class="metrics-table">
            <tbody>
              <tr><td>Debt/Equity</td><td>{{ data.debt_equity != null ? data.debt_equity.toFixed(1) + '%' : 'N/A' }}</td></tr>
              <tr><td>Current Ratio</td><td>{{ fmt(data.current_ratio, 'x') }}</td></tr>
              <tr><td>Quick Ratio</td><td>{{ fmt(data.quick_ratio, 'x') }}</td></tr>
              <tr><td>Free Cash Flow</td><td :class="pctClass(data.fcf)">{{ formatBillions(data.fcf) }}</td></tr>
              <tr><td>Готівка</td><td>{{ formatBillions(data.total_cash) }}</td></tr>
              <tr><td>Борг</td><td>{{ formatBillions(data.total_debt) }}</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Per-share & other -->
        <div class="metrics-card">
          <h3>📋 На акцію / Інше</h3>
          <table class="metrics-table">
            <tbody>
              <tr><td>EPS (trailing)</td><td>{{ data.eps_trailing != null ? '$' + data.eps_trailing.toFixed(2) : 'N/A' }}</td></tr>
              <tr><td>EPS (forward)</td><td>{{ data.eps_forward != null ? '$' + data.eps_forward.toFixed(2) : 'N/A' }}</td></tr>
              <tr><td>Book Value</td><td>{{ data.book_value != null ? '$' + data.book_value.toFixed(2) : 'N/A' }}</td></tr>
              <tr><td>Beta</td><td>{{ fmt(data.beta) }}</td></tr>
              <tr><td>Дивіденди</td><td>{{ fmt(data.div_yield, '%') }}</td></tr>
              <tr><td>Payout Ratio</td><td>{{ fmt(data.payout_ratio, '%') }}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- AI Analysis -->
      <div class="analysis-card">
        <div class="analysis-header">
          <span>🤖 Аналіз Claude</span>
          <span class="analysis-date">{{ formatDate(data.generated_at) }}</span>
        </div>
        <div class="analysis-body" v-html="renderMarkdown(data.analysis)" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const ticker = ref('')
const loading = ref(false)
const error = ref('')
const data = ref<any>(null)

async function analyze(force = false) {
  const t = ticker.value.trim().toUpperCase()
  if (!t) return

  loading.value = true
  error.value = ''

  try {
    const forceParam = force === true ? '&force=true' : ''
    const res = await $fetch(`/api/stock/analyze?ticker=${t}${forceParam}`)
    data.value = res
  } catch (e: any) {
    const detail = e?.data?.detail || e?.message || 'Невідома помилка'
    error.value = detail
    data.value = null
  } finally {
    loading.value = false
  }
}

// --- Formatters ---

function fmt(val: number | null, type = '') {
  if (val == null) return 'N/A'
  if (type === '%') return (val * 100).toFixed(1) + '%'
  if (type === 'x') return val.toFixed(2) + 'x'
  return val.toFixed(2)
}

function formatBillions(val: number | null) {
  if (val == null) return 'N/A'
  const abs = Math.abs(val)
  const sign = val < 0 ? '-' : ''
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(2)}B`
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(1)}M`
  return `${sign}$${abs.toLocaleString()}`
}

function formatDate(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('uk-UA', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function pctClass(val: number | null) {
  if (val == null) return ''
  return val >= 0 ? 'positive' : 'negative'
}

function renderMarkdown(text: string) {
  if (!text) return ''
  return text
    // headers
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    // bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // line breaks
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.stock-analyzer {
  padding: 20px 0;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--color-text, #e2e8f0);
}

/* Search */
.search-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.ticker-input {
  flex: 1;
  max-width: 280px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--color-border, #334155);
  background: var(--color-surface, #1e293b);
  color: var(--color-text, #e2e8f0);
  font-size: 1rem;
  font-family: monospace;
  letter-spacing: 0.05em;
  outline: none;
  transition: border-color 0.15s;
}
.ticker-input:focus {
  border-color: #3b82f6;
}

.analyze-btn {
  padding: 10px 20px;
  border-radius: 8px;
  background: #3b82f6;
  color: #fff;
  border: none;
  font-weight: 600;
  cursor: pointer;
  min-width: 120px;
  transition: background 0.15s;
}
.analyze-btn:hover:not(:disabled) { background: #2563eb; }
.analyze-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.refresh-btn {
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--color-surface, #1e293b);
  border: 1px solid var(--color-border, #334155);
  color: var(--color-text, #e2e8f0);
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.15s;
}
.refresh-btn:hover:not(:disabled) { background: #334155; }

/* Spinner */
.spinner {
  display: inline-block;
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Error */
.error-box {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
}

/* Skeleton */
.skeleton-wrap { margin-top: 8px; }
.skeleton {
  background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
  background-size: 200% 100%;
  border-radius: 8px;
  animation: shimmer 1.2s infinite;
}
@keyframes shimmer { to { background-position: -200% 0; } }

/* Company header */
.company-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 14px 16px;
  background: var(--color-surface, #1e293b);
  border-radius: 10px;
  border: 1px solid var(--color-border, #334155);
}
.company-info { display: flex; align-items: center; gap: 10px; }
.ticker-badge {
  font-family: monospace;
  font-size: 1.2rem;
  font-weight: 700;
  color: #60a5fa;
}
.company-name { font-size: 1rem; color: var(--color-text, #e2e8f0); }
.company-meta { display: flex; flex-wrap: wrap; gap: 6px; }

.badge {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.25);
}
.badge.muted { background: rgba(100,116,139,0.15); color: #94a3b8; border-color: rgba(100,116,139,0.2); }
.badge.green { background: rgba(34,197,94,0.12); color: #86efac; border-color: rgba(34,197,94,0.2); }

/* Metrics grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.metrics-card {
  background: var(--color-surface, #1e293b);
  border: 1px solid var(--color-border, #334155);
  border-radius: 10px;
  padding: 14px 16px;
}
.metrics-card h3 {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748b;
  margin: 0 0 10px;
}

.metrics-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.metrics-table td {
  padding: 5px 0;
  color: var(--color-text, #e2e8f0);
}
.metrics-table td:first-child { color: #94a3b8; }
.metrics-table td:last-child { text-align: right; font-family: monospace; }
.metrics-table tr + tr td { border-top: 1px solid rgba(51,65,85,0.5); }

.positive { color: #4ade80 !important; }
.negative { color: #f87171 !important; }

/* AI Analysis */
.analysis-card {
  background: var(--color-surface, #1e293b);
  border: 1px solid var(--color-border, #334155);
  border-radius: 10px;
  overflow: hidden;
}
.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(59, 130, 246, 0.08);
  border-bottom: 1px solid var(--color-border, #334155);
  font-weight: 600;
  color: #93c5fd;
  font-size: 0.9rem;
}
.analysis-date { font-size: 0.75rem; color: #64748b; font-weight: 400; }
.analysis-body {
  padding: 16px;
  color: var(--color-text, #cbd5e1);
  font-size: 0.9rem;
  line-height: 1.7;
}
.analysis-body :deep(h3) {
  font-size: 0.95rem;
  color: #e2e8f0;
  margin: 14px 0 6px;
}
.analysis-body :deep(h4) {
  font-size: 0.875rem;
  color: #93c5fd;
  margin: 12px 0 4px;
}
.analysis-body :deep(strong) { color: #f1f5f9; }
</style>
