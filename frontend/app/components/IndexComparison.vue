<template>
  <div class="bg-gray-900 rounded-2xl p-6">

    <!-- Header -->
    <div class="flex items-center justify-between mb-5 flex-wrap gap-3">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">S&amp;P 500 vs MSCI World</h2>
        <p v-if="fetchedAt" class="text-xs text-gray-500 mt-0.5">Оновлено {{ formatDateTime(fetchedAt) }}</p>
      </div>

      <!-- Period tabs -->
      <div class="flex gap-1">
        <button
          v-for="p in periods"
          :key="p.key"
          @click="selectedPeriod = p.key"
          class="px-3 py-1 rounded-lg text-xs font-medium transition-colors"
          :class="selectedPeriod === p.key
            ? 'bg-blue-600 text-white'
            : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'"
        >
          {{ p.label }}
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-40 text-gray-500 text-sm">
      Завантаження даних…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-40 text-red-400 text-sm">
      {{ error }}
    </div>

    <template v-else-if="sp500 && msciWorld">

      <!-- SVG Chart -->
      <div class="mb-5">
        <!-- Legend -->
        <div class="flex gap-5 mb-3 text-xs text-gray-400">
          <span class="flex items-center gap-1.5">
            <span class="w-6 h-0.5 inline-block bg-blue-500 rounded"></span>
            S&amp;P 500
          </span>
          <span class="flex items-center gap-1.5">
            <span class="w-6 h-0.5 inline-block bg-yellow-400 rounded"></span>
            MSCI World
          </span>
        </div>

        <svg viewBox="0 0 400 130" class="w-full" preserveAspectRatio="none" style="height: 160px;">
          <!-- Baseline at 100 -->
          <line
            :x1="PAD_L" :y1="yForValue(100)"
            :x2="400 - PAD_R" :y2="yForValue(100)"
            stroke="#374151" stroke-width="0.5" stroke-dasharray="3,3"
          />

          <!-- MSCI World line -->
          <polyline
            :points="msciPoints"
            fill="none"
            stroke="#eab308"
            stroke-width="1.5"
            stroke-linejoin="round"
            stroke-linecap="round"
          />

          <!-- S&P 500 line -->
          <polyline
            :points="sp500Points"
            fill="none"
            stroke="#3b82f6"
            stroke-width="1.5"
            stroke-linejoin="round"
            stroke-linecap="round"
          />
        </svg>
      </div>

      <!-- Cards -->
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div class="rounded-xl bg-gray-800/60 p-4">
          <p class="text-xs text-gray-500 mb-1">S&amp;P 500</p>
          <p class="text-xl font-bold text-white">${{ formatPrice(sp500.current_price) }}</p>
          <p class="text-sm mt-1" :class="sp500.return_pct >= 0 ? 'text-green-400' : 'text-red-400'">
            {{ sp500.return_pct >= 0 ? '+' : '' }}{{ sp500.return_pct.toFixed(2) }}%
            <span class="text-gray-600 text-xs ml-1">за {{ periodLabel }}</span>
          </p>
        </div>

        <div class="rounded-xl bg-gray-800/60 p-4">
          <p class="text-xs text-gray-500 mb-1">MSCI World (IWDA.L)</p>
          <p class="text-xl font-bold text-white">${{ formatPrice(msciWorld.current_price) }}</p>
          <p class="text-sm mt-1" :class="msciWorld.return_pct >= 0 ? 'text-green-400' : 'text-red-400'">
            {{ msciWorld.return_pct >= 0 ? '+' : '' }}{{ msciWorld.return_pct.toFixed(2) }}%
            <span class="text-gray-600 text-xs ml-1">за {{ periodLabel }}</span>
          </p>
        </div>
      </div>

      <!-- Winner row -->
      <div class="rounded-xl px-4 py-3 text-sm text-center font-medium"
           :class="winnerBg">
        <span :class="winnerColor">{{ winnerText }}</span>
      </div>

    </template>

  </div>
</template>

<script setup lang="ts">
const { getIndexComparison } = useApi()

const { data: rawData, error: fetchError, pending: loading } = await useAsyncData(
  'index-comparison',
  () => getIndexComparison().catch(() => null) as Promise<any[] | null>
)

const error = computed(() => {
  if (!fetchError.value) return null
  const status = (fetchError.value as any)?.response?.status
  if (status === 404) return 'Дані ще не завантажено. Запустіть POST /api/collect/index_comparison'
  return 'Помилка завантаження даних індексів'
})

const periods = [
  { key: '1mo', label: '1М' },
  { key: '3mo', label: '3М' },
  { key: 'ytd', label: 'YTD' },
  { key: '1y',  label: '1Р' },
]

const selectedPeriod = ref('1mo')

const byTicker = computed(() => {
  const result: Record<string, Record<string, any>> = {}
  for (const row of (rawData.value ?? [])) {
    if (!result[row.ticker]) result[row.ticker] = {}
    result[row.ticker][row.period] = row
  }
  return result
})

const sp500 = computed(() => byTicker.value?.['sp500']?.[selectedPeriod.value] ?? null)
const msciWorld = computed(() => byTicker.value?.['msci_world']?.[selectedPeriod.value] ?? null)

const fetchedAt = computed(() => sp500.value?.fetched_at ?? null)

const periodLabel = computed(() => periods.find(p => p.key === selectedPeriod.value)?.label ?? selectedPeriod.value)

// Chart geometry
const PAD_L = 4
const PAD_R = 4
const PAD_T = 8
const PAD_B = 8
const CHART_W = 400 - PAD_L - PAD_R
const CHART_H = 130 - PAD_T - PAD_B

function chartExtremes(sp: any, msci: any): { min: number; max: number } {
  const all: number[] = [
    ...(sp?.chart_data ?? []).map((p: any) => p.value),
    ...(msci?.chart_data ?? []).map((p: any) => p.value),
  ]
  if (!all.length) return { min: 95, max: 105 }
  const min = Math.min(...all)
  const max = Math.max(...all)
  const pad = (max - min) * 0.05 || 1
  return { min: min - pad, max: max + pad }
}

const extremes = computed(() => chartExtremes(sp500.value, msciWorld.value))

function yForValue(val: number): number {
  const { min, max } = extremes.value
  const ratio = (val - min) / (max - min)
  return PAD_T + CHART_H * (1 - ratio)
}

function toPoints(data: Array<{ date: string; value: number }>): string {
  if (!data || data.length < 2) return ''
  return data.map((p, i) => {
    const x = PAD_L + (i / (data.length - 1)) * CHART_W
    const y = yForValue(p.value)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

const sp500Points = computed(() => toPoints(sp500.value?.chart_data ?? []))
const msciPoints = computed(() => toPoints(msciWorld.value?.chart_data ?? []))

// Winner
const diff = computed(() => {
  if (!sp500.value || !msciWorld.value) return 0
  return sp500.value.return_pct - msciWorld.value.return_pct
})

const winnerText = computed(() => {
  const d = diff.value
  if (Math.abs(d) < 0.01) return 'Індекси показують однаковий результат'
  if (d > 0) return `S&P 500 випереджає на ${Math.abs(d).toFixed(2)}%`
  return `MSCI World випереджає на ${Math.abs(d).toFixed(2)}%`
})

const winnerBg = computed(() => {
  const d = diff.value
  if (Math.abs(d) < 0.01) return 'bg-gray-800/60'
  if (d > 0) return 'bg-blue-950/50'
  return 'bg-yellow-950/50'
})

const winnerColor = computed(() => {
  const d = diff.value
  if (Math.abs(d) < 0.01) return 'text-gray-400'
  if (d > 0) return 'text-blue-400'
  return 'text-yellow-400'
})

function formatPrice(v: number): string {
  if (v >= 1000) return v.toLocaleString('en-US', { maximumFractionDigits: 0 })
  return v.toFixed(2)
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

</script>
