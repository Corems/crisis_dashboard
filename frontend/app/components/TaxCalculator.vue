<template>
  <div class="bg-gray-900 rounded-2xl p-6">

    <!-- Header -->
    <div class="mb-5">
      <h2 class="text-lg font-semibold text-gray-100">Калькулятор податку на інвестиції</h2>
      <p class="text-xs text-gray-500 mt-0.5">ПДФО + Військовий збір з прибутку від продажу ЦП (Україна)</p>
    </div>

    <!-- Tax rate settings -->
    <div class="bg-gray-800/50 rounded-xl p-4 mb-6 flex flex-wrap items-center gap-4">
      <span class="text-sm text-gray-400 font-medium">Ставки оподаткування:</span>
      <label class="flex items-center gap-2 text-sm text-gray-300">
        ПДФО
        <input
          v-model.number="pdfo"
          type="number" min="0" max="100" step="0.5"
          class="tax-input w-16 text-center"
        />
        %
      </label>
      <label class="flex items-center gap-2 text-sm text-gray-300">
        Військовий збір
        <input
          v-model.number="vz"
          type="number" min="0" max="100" step="0.5"
          class="tax-input w-16 text-center"
        />
        %
      </label>
      <div class="ml-auto flex items-center gap-2">
        <span class="text-xs text-gray-500">Загальна ставка:</span>
        <span class="text-lg font-bold text-yellow-400">{{ totalRate.toFixed(1) }}%</span>
      </div>
    </div>

    <!-- Positions -->
    <div v-for="(pos, i) in positions" :key="pos.id" class="bg-gray-800/40 rounded-xl p-4 mb-4">

      <!-- Row 1: ticker, lots, commission, remove -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
        <div>
          <p class="text-xs text-gray-500 mb-1">Тікер</p>
          <input v-model="pos.ticker" type="text" placeholder="VUAA.L" class="tax-input" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1">Кількість лотів</p>
          <input v-model.number="pos.lots" type="number" min="1" step="1" class="tax-input" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1">Комісія брокера $</p>
          <input v-model.number="pos.commission" type="number" min="0" step="0.01" class="tax-input" />
        </div>
        <div class="flex items-end">
          <button
            @click="removePosition(pos.id)"
            class="w-full py-2 rounded-lg text-sm text-red-400 bg-red-950/30 hover:bg-red-950/60 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            ✕ Видалити
          </button>
        </div>
      </div>

      <!-- Row 2: buy/sell prices + rates -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div>
          <p class="text-xs text-gray-500 mb-1">Ціна купівлі $</p>
          <input v-model.number="pos.buyPrice" type="number" min="0" step="0.01" class="tax-input" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1">Курс ₴/$ на купівлю</p>
          <input v-model.number="pos.buyRate" type="number" min="0" step="0.01" class="tax-input" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1">Ціна продажу $</p>
          <input v-model.number="pos.sellPrice" type="number" min="0" step="0.01" class="tax-input" />
        </div>
        <div>
          <p class="text-xs text-gray-500 mb-1">Курс ₴/$ на продаж</p>
          <input v-model.number="pos.sellRate" type="number" min="0" step="0.01" class="tax-input" />
        </div>
      </div>

      <!-- Results -->
      <div class="bg-gray-900/60 rounded-lg p-3 mt-3">
        <p class="text-xs text-gray-600 mb-2 font-medium uppercase tracking-wider">Розрахунок</p>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-2">
          <div>
            <p class="text-xs text-gray-500">Продаж (₴)</p>
            <p class="text-sm font-semibold text-white">{{ fmtUAH(results[i].sell_uah) }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Купівля (₴)</p>
            <p class="text-sm font-semibold text-white">{{ fmtUAH(results[i].buy_uah) }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Вал. прибуток ₴</p>
            <p class="text-sm font-semibold" :class="results[i].gross_profit_uah >= 0 ? 'text-green-400' : 'text-red-400'">
              {{ fmtUAHSigned(results[i].gross_profit_uah) }}
            </p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Вал. прибуток $</p>
            <p class="text-sm font-semibold" :class="results[i].gross_profit_usd >= 0 ? 'text-green-400' : 'text-red-400'">
              {{ fmtUSDSigned(results[i].gross_profit_usd) }}
            </p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Податок ({{ totalRate.toFixed(1) }}%)</p>
            <p class="text-sm font-semibold text-orange-400">{{ fmtUAH(results[i].tax_uah) }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Чистий прибуток ₴</p>
            <p class="text-sm font-semibold" :class="results[i].net_profit_uah >= 0 ? 'text-green-400' : 'text-red-400'">
              {{ fmtUAHSigned(results[i].net_profit_uah) }}
            </p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Чистий прибуток $</p>
            <p class="text-sm font-semibold" :class="results[i].net_profit_usd >= 0 ? 'text-green-400' : 'text-red-400'">
              {{ fmtUSDSigned(results[i].net_profit_usd) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Warning: USD loss but UAH profit — tax still owed -->
      <div
        v-if="results[i].usd_loss_uah_profit"
        class="mt-3 bg-red-950/40 border border-red-900/50 rounded-lg px-4 py-2.5 flex items-start gap-2"
      >
        <span class="shrink-0">⚠️</span>
        <span class="text-sm text-red-300">
          <strong>Збиток у USD, але прибуток у гривні</strong> — через девальвацію гривні
          податок все одно сплачується ({{ fmtUAH(results[i].tax_uah) }})
        </span>
      </div>

      <!-- Info: USD profit but UAH loss — no tax -->
      <div
        v-if="results[i].usd_profit_uah_loss"
        class="mt-3 bg-blue-950/40 border border-blue-900/50 rounded-lg px-4 py-2.5 flex items-start gap-2"
      >
        <span class="shrink-0">ℹ️</span>
        <span class="text-sm text-blue-300">
          <strong>Прибуток у USD, але збиток у гривні</strong> — через зміцнення гривні
          податок не сплачується
        </span>
      </div>

    </div>

    <!-- Add position button -->
    <button
      @click="addPosition"
      class="w-full py-3 rounded-xl text-sm font-medium text-blue-400 bg-blue-950/30 hover:bg-blue-950/60 border border-blue-900/40 hover:border-blue-700 transition-colors mb-6"
    >
      + Додати позицію
    </button>

    <!-- Summary totals -->
    <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-5">
      <div class="rounded-xl bg-gray-800/60 p-4">
        <p class="text-xs text-gray-500 mb-1">Сума продажу (₴)</p>
        <p class="text-base font-bold text-white">{{ fmtUAH(totals.sell_uah) }}</p>
      </div>
      <div class="rounded-xl p-4" :class="totals.gross_uah >= 0 ? 'bg-green-950/30' : 'bg-red-950/30'">
        <p class="text-xs text-gray-500 mb-1">Вал. прибуток (₴)</p>
        <p class="text-base font-bold" :class="totals.gross_uah >= 0 ? 'text-green-400' : 'text-red-400'">
          {{ fmtUAHSigned(totals.gross_uah) }}
        </p>
      </div>
      <div class="rounded-xl p-4" :class="totals.gross_usd >= 0 ? 'bg-green-950/30' : 'bg-red-950/30'">
        <p class="text-xs text-gray-500 mb-1">Вал. прибуток ($)</p>
        <p class="text-base font-bold" :class="totals.gross_usd >= 0 ? 'text-green-400' : 'text-red-400'">
          {{ fmtUSDSigned(totals.gross_usd) }}
        </p>
      </div>
      <div class="rounded-xl bg-orange-950/30 p-4">
        <p class="text-xs text-gray-500 mb-1">Загальний податок (₴)</p>
        <p class="text-base font-bold text-orange-400">{{ fmtUAH(totals.tax_uah) }}</p>
      </div>
      <div class="rounded-xl p-4" :class="totals.net_uah >= 0 ? 'bg-green-950/40' : 'bg-red-950/40'">
        <p class="text-xs text-gray-500 mb-1">Чистий прибуток (₴)</p>
        <p class="text-base font-bold" :class="totals.net_uah >= 0 ? 'text-green-400' : 'text-red-400'">
          {{ fmtUAHSigned(totals.net_uah) }}
        </p>
      </div>
      <div class="rounded-xl p-4" :class="totals.net_usd >= 0 ? 'bg-green-950/40' : 'bg-red-950/40'">
        <p class="text-xs text-gray-500 mb-1">Чистий прибуток ($)</p>
        <p class="text-base font-bold" :class="totals.net_usd >= 0 ? 'text-green-400' : 'text-red-400'">
          {{ fmtUSDSigned(totals.net_usd) }}
        </p>
      </div>
    </div>

    <!-- Disclaimer -->
    <p class="text-xs text-gray-600 leading-relaxed border-t border-gray-800 pt-4">
      Розрахунок носить інформаційний характер. Прибуток визначається у гривні за офіційним курсом НБУ
      на дату кожної операції. Комісія брокера конвертується за курсом на дату продажу.
      Проконсультуйтесь з податковим консультантом.
    </p>

  </div>
</template>

<script setup lang="ts">
// ── Tax rates ─────────────────────────────────────────────────────────────────
const pdfo = ref(18)
const vz = ref(1.5)
const totalRate = computed(() => pdfo.value + vz.value)

// ── Positions ─────────────────────────────────────────────────────────────────
let nextId = 1

interface Position {
  id: number
  ticker: string
  buyPrice: number
  buyRate: number
  sellPrice: number
  sellRate: number
  lots: number
  commission: number
}

function makePosition(overrides: Partial<Position> = {}): Position {
  return {
    id: nextId++,
    ticker: '',
    buyPrice: 0,
    buyRate: 41.5,
    sellPrice: 0,
    sellRate: 41.5,
    lots: 1,
    commission: 0,
    ...overrides,
  }
}

const positions = ref<Position[]>([makePosition()])

function addPosition() {
  positions.value.push(makePosition())
}

function removePosition(id: number) {
  if (positions.value.length === 1) return
  positions.value = positions.value.filter(p => p.id !== id)
}

// ── Calculation ───────────────────────────────────────────────────────────────
function calcPosition(pos: Position, rate: number) {
  const buyPrice   = pos.buyPrice   || 0
  const sellPrice  = pos.sellPrice  || 0
  const buyRate    = pos.buyRate    || 1
  const sellRate   = pos.sellRate   || 1
  const lots       = pos.lots       || 0
  const commission = pos.commission || 0

  const buy_uah        = buyPrice * lots * buyRate
  const sell_uah       = sellPrice * lots * sellRate
  const commission_uah = commission * sellRate     // commission paid at sell → sell rate

  const gross_profit_uah = sell_uah - buy_uah - commission_uah
  const gross_profit_usd = (sellPrice - buyPrice) * lots - commission

  const tax_uah      = gross_profit_uah > 0 ? gross_profit_uah * rate / 100 : 0
  const net_profit_uah = gross_profit_uah - tax_uah
  const net_profit_usd = net_profit_uah / sellRate

  return {
    buy_uah,
    sell_uah,
    commission_uah,
    gross_profit_uah,
    gross_profit_usd,
    tax_uah,
    net_profit_uah,
    net_profit_usd,
    // Warning flags
    usd_loss_uah_profit: gross_profit_usd < 0 && gross_profit_uah > 0,
    usd_profit_uah_loss: gross_profit_usd > 0 && gross_profit_uah <= 0,
  }
}

const results = computed(() =>
  positions.value.map(pos => calcPosition(pos, totalRate.value))
)

const totals = computed(() => {
  const r = results.value
  return {
    sell_uah:  r.reduce((s, x) => s + x.sell_uah, 0),
    gross_uah: r.reduce((s, x) => s + x.gross_profit_uah, 0),
    gross_usd: r.reduce((s, x) => s + x.gross_profit_usd, 0),
    tax_uah:   r.reduce((s, x) => s + x.tax_uah, 0),
    net_uah:   r.reduce((s, x) => s + x.net_profit_uah, 0),
    net_usd:   r.reduce((s, x) => s + x.net_profit_usd, 0),
  }
})

// ── Formatters ────────────────────────────────────────────────────────────────
function fmtUAH(v: number): string {
  const abs = Math.abs(v)
  return abs.toLocaleString('uk-UA', { maximumFractionDigits: 0 }) + ' ₴'
}

function fmtUAHSigned(v: number): string {
  const sign = v < 0 ? '−' : '+'
  return sign + fmtUAH(v)
}

function fmtUSD(v: number): string {
  const abs = Math.abs(v)
  if (abs >= 10_000) return '$' + abs.toLocaleString('en-US', { maximumFractionDigits: 0 })
  return '$' + abs.toFixed(2)
}

function fmtUSDSigned(v: number): string {
  const sign = v < 0 ? '−' : '+'
  return sign + fmtUSD(v)
}
</script>

<style scoped>
.tax-input {
  @apply w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm;
  @apply focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500;
  @apply tabular-nums;
}
</style>
