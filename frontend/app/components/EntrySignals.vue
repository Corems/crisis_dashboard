<template>
  <div class="bg-gray-900 rounded-2xl p-6">

    <div class="flex items-start justify-between mb-5 flex-wrap gap-2">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">Сигнали входу в S&amp;P 500</h2>
        <p v-if="data" class="text-xs text-gray-500 mt-0.5">Оновлено {{ formatTime(data.fetched_at) }}</p>
      </div>
      <span class="text-xs text-gray-600 mt-1">Yahoo / FRED / DB</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-32 text-gray-500 text-sm">
      Обчислення сигналів…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-32 text-red-400 text-sm">
      {{ error }}
    </div>

    <template v-else-if="data">

      <!-- Signal rows -->
      <div class="flex flex-col gap-2 mb-5">
        <div
          v-for="sig in signals"
          :key="sig.key"
          class="flex items-center justify-between rounded-xl px-4 py-3"
          :class="sig.ok ? 'bg-green-950/40' : 'bg-gray-800/50'"
        >
          <div class="flex items-center gap-3">
            <span class="text-lg">{{ sig.ok ? '✅' : '❌' }}</span>
            <span class="text-sm text-gray-200">{{ sig.label }}</span>
          </div>
          <span
            v-if="sig.current !== null"
            class="text-xs font-medium tabular-nums"
            :class="sig.ok ? 'text-green-400' : 'text-red-400'"
          >
            {{ sig.current }}
          </span>
        </div>
      </div>

      <!-- Overall signal badge -->
      <div
        class="rounded-xl px-5 py-4 flex items-center justify-between"
        :class="overallBg"
      >
        <div class="flex items-center gap-3">
          <span class="text-2xl">{{ overallIcon }}</span>
          <div>
            <p class="text-base font-bold" :class="overallColor">{{ overallLabel }}</p>
            <p class="text-xs text-gray-500">{{ data.green_count }}/5 сигналів зелені</p>
          </div>
        </div>
        <!-- Mini bar -->
        <div class="flex gap-1">
          <div
            v-for="i in 5"
            :key="i"
            class="w-3 h-3 rounded-full"
            :class="i <= data.green_count ? 'bg-green-400' : 'bg-gray-700'"
          />
        </div>
      </div>

    </template>
  </div>
</template>

<script setup lang="ts">
const { getMarketSignals } = useApi()

const { data: rawData, error: fetchError, pending: loading } = await useAsyncData(
  'market-signals',
  () => getMarketSignals().catch(() => null) as Promise<any | null>
)

const data = computed(() => rawData.value as any ?? null)

const error = computed(() => {
  if (!fetchError.value) return null
  const status = (fetchError.value as any)?.response?.status
  if (status === 404) return 'Дані ще не завантажено. Запустіть POST /api/collect/signals'
  return 'Помилка завантаження сигналів'
})

const signals = computed(() => {
  if (!data.value) return []
  const d = data.value
  return [
    {
      key: 'vix',
      label: 'VIX < 20',
      ok: d.vix_ok,
      current: d.vix != null ? d.vix.toFixed(1) : null,
    },
    {
      key: 'fg',
      label: 'Fear & Greed > 30',
      ok: d.fear_greed_ok,
      current: d.fear_greed_score != null ? Math.round(d.fear_greed_score).toString() : null,
    },
    {
      key: 'ma200',
      label: 'S&P 500 вище 200MA',
      ok: d.sp500_above_ma200,
      current: d.sp500_current != null && d.sp500_ma200 != null
        ? `$${formatNum(d.sp500_current)} / MA: $${formatNum(d.sp500_ma200)}`
        : null,
    },
    {
      key: 'cape',
      label: 'CAPE < 25',
      ok: d.cape_ok,
      current: d.cape != null ? d.cape.toFixed(1) : null,
    },
    {
      key: 'cot',
      label: 'COT нафта net > 0',
      ok: d.cot_crude_ok,
      current: d.cot_crude_net != null ? formatNet(d.cot_crude_net) : null,
    },
  ]
})

function formatNum(v: number): string {
  return v >= 1000 ? v.toLocaleString('en-US', { maximumFractionDigits: 0 }) : v.toFixed(2)
}

function formatNet(v: number): string {
  const abs = Math.abs(v)
  const sign = v >= 0 ? '+' : '−'
  if (abs >= 1_000_000) return sign + (abs / 1_000_000).toFixed(1) + 'M'
  if (abs >= 1_000) return sign + (abs / 1_000).toFixed(0) + 'K'
  return sign + abs.toString()
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const overallLabel = computed(() => {
  if (!data.value) return ''
  return { WAIT: 'ЧЕКАТИ', WATCH: 'ПРИДИВЛЯТИСЬ', ENTER: 'ВХОДИТИ' }[data.value.overall_signal] ?? data.value.overall_signal
})

const overallIcon = computed(() => {
  if (!data.value) return ''
  return { WAIT: '🔴', WATCH: '🟡', ENTER: '🟢' }[data.value.overall_signal] ?? '⚪'
})

const overallColor = computed(() => {
  if (!data.value) return 'text-gray-400'
  return { WAIT: 'text-red-400', WATCH: 'text-yellow-400', ENTER: 'text-green-400' }[data.value.overall_signal] ?? 'text-gray-400'
})

const overallBg = computed(() => {
  if (!data.value) return 'bg-gray-800/60'
  return { WAIT: 'bg-red-950/40', WATCH: 'bg-yellow-950/40', ENTER: 'bg-green-950/40' }[data.value.overall_signal] ?? 'bg-gray-800/60'
})
</script>
