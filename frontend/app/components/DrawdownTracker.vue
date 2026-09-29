<template>
  <div class="bg-gray-900 rounded-2xl p-6">

    <div class="flex items-start justify-between mb-5">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">Просадка від ATH</h2>
        <p v-if="data" class="text-xs text-gray-500 mt-0.5">Оновлено {{ formatTime(data.fetched_at) }}</p>
      </div>
      <span class="text-xs text-gray-600 mt-1">2-річний максимум</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-32 text-gray-500 text-sm">
      Завантаження даних…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-32 text-red-400 text-sm">
      {{ error }}
    </div>

    <template v-else-if="data">
      <div class="grid grid-cols-2 gap-4">

        <!-- S&P 500 -->
        <div class="rounded-xl bg-gray-800/50 p-4">
          <p class="text-xs text-gray-500 mb-3 font-medium">S&amp;P 500</p>

          <div class="flex justify-between text-xs text-gray-400 mb-1">
            <span>ATH</span>
            <span class="text-white font-medium">${{ formatPrice(data.sp500_ath) }}</span>
          </div>
          <div class="flex justify-between text-xs text-gray-400 mb-3">
            <span>Зараз</span>
            <span class="text-white font-medium">${{ formatPrice(data.sp500_current) }}</span>
          </div>

          <p
            class="text-2xl font-bold mb-3"
            :class="drawdownColor(data.sp500_drawdown_pct)"
          >
            📉 {{ data.sp500_drawdown_pct != null ? data.sp500_drawdown_pct.toFixed(1) + '%' : '—' }}
          </p>

          <!-- Severity bar -->
          <template v-if="data.sp500_drawdown_pct != null">
            <div class="h-2 rounded-full bg-gray-700 overflow-hidden mb-1">
              <div
                class="h-full rounded-full transition-all"
                :class="barColor(data.sp500_drawdown_pct)"
                :style="{ width: barWidth(data.sp500_drawdown_pct) }"
              />
            </div>
            <p class="text-xs font-medium" :class="drawdownColor(data.sp500_drawdown_pct)">
              {{ drawdownLabel(data.sp500_drawdown_pct) }}
            </p>
          </template>
        </div>

        <!-- MSCI World -->
        <div class="rounded-xl bg-gray-800/50 p-4">
          <p class="text-xs text-gray-500 mb-3 font-medium">MSCI World (IWDA.L)</p>

          <div class="flex justify-between text-xs text-gray-400 mb-1">
            <span>ATH</span>
            <span class="text-white font-medium">${{ formatPrice(data.msci_ath) }}</span>
          </div>
          <div class="flex justify-between text-xs text-gray-400 mb-3">
            <span>Зараз</span>
            <span class="text-white font-medium">${{ formatPrice(data.msci_current) }}</span>
          </div>

          <p
            class="text-2xl font-bold mb-3"
            :class="drawdownColor(data.msci_drawdown_pct)"
          >
            📉 {{ data.msci_drawdown_pct != null ? data.msci_drawdown_pct.toFixed(1) + '%' : '—' }}
          </p>

          <template v-if="data.msci_drawdown_pct != null">
            <div class="h-2 rounded-full bg-gray-700 overflow-hidden mb-1">
              <div
                class="h-full rounded-full transition-all"
                :class="barColor(data.msci_drawdown_pct)"
                :style="{ width: barWidth(data.msci_drawdown_pct) }"
              />
            </div>
            <p class="text-xs font-medium" :class="drawdownColor(data.msci_drawdown_pct)">
              {{ drawdownLabel(data.msci_drawdown_pct) }}
            </p>
          </template>
        </div>

      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
const { getMarketSignals } = useApi()

// Same key as EntrySignals — Nuxt deduplicates the fetch
const { data: rawData, error: fetchError, pending: loading } = await useAsyncData(
  'market-signals',
  () => getMarketSignals().catch(() => null) as Promise<any | null>
)

const data = computed(() => rawData.value as any ?? null)

const error = computed(() => {
  if (!fetchError.value) return null
  const status = (fetchError.value as any)?.response?.status
  if (status === 404) return 'Дані ще не завантажено. Запустіть POST /api/collect/signals'
  return 'Помилка завантаження даних'
})

function formatPrice(v: number | null | undefined): string {
  if (v == null) return '—'
  return v >= 1000 ? v.toLocaleString('en-US', { maximumFractionDigits: 0 }) : v.toFixed(2)
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// drawdown_pct is always negative (e.g. -8.4)
function absDD(pct: number | null): number {
  return pct != null ? Math.abs(pct) : 0
}

function drawdownLabel(pct: number | null): string {
  const a = absDD(pct)
  if (a < 10) return 'Норма'
  if (a < 20) return 'Корекція'
  if (a < 35) return 'Ведмежий ринок'
  return 'Крах'
}

function drawdownColor(pct: number | null): string {
  const a = absDD(pct)
  if (a < 10) return 'text-green-400'
  if (a < 20) return 'text-yellow-400'
  if (a < 35) return 'text-orange-400'
  return 'text-red-400'
}

function barColor(pct: number | null): string {
  const a = absDD(pct)
  if (a < 10) return 'bg-green-500'
  if (a < 20) return 'bg-yellow-400'
  if (a < 35) return 'bg-orange-400'
  return 'bg-red-500'
}

// Bar fills based on severity: 0% = empty, 35%+ = full
function barWidth(pct: number | null): string {
  const a = Math.min(absDD(pct), 40)
  return (a / 40 * 100).toFixed(1) + '%'
}
</script>
