<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <div class="flex items-start justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">Позиції великих трейдерів (COT)</h2>
        <p v-if="reportDate" class="text-xs text-gray-500 mt-0.5">
          Звіт за {{ formatDate(reportDate) }} · Щотижневий звіт CFTC
        </p>
      </div>
      <span class="text-xs text-gray-600 mt-1">CFTC</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-24 text-gray-500 text-sm">
      Завантаження даних CFTC…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-24 text-red-400 text-sm">
      {{ error }}
    </div>

    <!-- Cards -->
    <div v-else-if="data.length" class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <div
        v-for="item in data"
        :key="item.instrument"
        class="rounded-xl p-4"
        :class="cardBg(item)"
      >
        <!-- Header -->
        <div class="flex items-center justify-between mb-2">
          <p class="text-xs font-semibold" :class="sentimentColor(item)">
            {{ instrumentLabel(item.instrument) }}
          </p>
          <span
            class="text-xs font-bold px-2 py-0.5 rounded"
            :class="sentimentBadge(item)"
          >
            {{ sentimentLabel(item) }}
          </span>
        </div>

        <!-- Net position -->
        <p class="text-xl font-bold text-white">
          {{ formatNet(item.noncomm_net) }}
        </p>
        <p class="text-xs text-gray-500 mb-2">нетто-позиція (контракти)</p>

        <!-- WoW change -->
        <p class="text-sm" :class="wowColor(item)">
          <span>{{ wowArrow(item) }}</span>
          {{ formatNet(item.net_change_wow) }}
          <span class="text-gray-600 text-xs ml-1">тижн. зміна</span>
        </p>

        <!-- Long / Short ratio bar -->
        <div class="mt-3">
          <div class="flex justify-between text-xs text-gray-500 mb-1">
            <span>Лонг {{ longPct(item) }}%</span>
            <span>Шорт {{ shortPct(item) }}%</span>
          </div>
          <div class="h-2 rounded-full bg-red-900/60 overflow-hidden">
            <div
              class="h-full rounded-full bg-green-500 transition-all"
              :style="{ width: longPct(item) + '%' }"
            />
          </div>
        </div>

        <!-- OI -->
        <p class="text-xs text-gray-600 mt-2">
          Відкр. інтерес: {{ formatNet(item.open_interest) }}
          <span v-if="item.noncomm_net_pct_oi != null" class="ml-1">
            ({{ item.noncomm_net_pct_oi.toFixed(1) }}% ВІ)
          </span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { getCotLatest } = useApi()

const { data: rawData, error: fetchError, pending: loading } = await useAsyncData(
  'cot-latest',
  () => getCotLatest() as Promise<any[]>
)

const data = computed(() => rawData.value ?? [])

const error = computed(() => {
  if (!fetchError.value) return null
  const status = (fetchError.value as any)?.response?.status
  if (status === 404) return 'Дані COT ще не завантажено. Запустіть POST /api/collect/cot'
  return 'Помилка завантаження даних CFTC'
})

const reportDate = computed(() => data.value[0]?.report_date ?? null)

const INSTRUMENT_LABELS: Record<string, string> = {
  crude_oil: 'Нафта (CL)',
  gold:      'Золото (GC)',
  sp500:     'S&P 500',
  euro:      'Євро (EUR)',
}

const instrumentLabel = (k: string) => INSTRUMENT_LABELS[k] ?? k

const formatDate = (d: string) =>
  new Date(d).toLocaleDateString('uk-UA', { year: 'numeric', month: 'long', day: 'numeric' })

const formatNet = (v: number | null) => {
  if (v == null) return '—'
  const abs = Math.abs(v)
  const sign = v >= 0 ? '+' : '−'
  if (abs >= 1_000_000) return sign + (abs / 1_000_000).toFixed(2) + 'M'
  if (abs >= 1_000)     return sign + (abs / 1_000).toFixed(1) + 'K'
  return sign + abs.toString()
}

const longPct = (item: any) => {
  const total = item.noncomm_long + item.noncomm_short
  if (!total) return 50
  return Math.round(item.noncomm_long / total * 100)
}

const shortPct = (item: any) => 100 - longPct(item)

// Sentiment: bullish if net > 0, bearish if net < 0
const isBullish = (item: any) => item.noncomm_net > 0
const isBearish = (item: any) => item.noncomm_net < 0

const sentimentLabel = (item: any) => {
  if (isBullish(item)) return 'Бичачий'
  if (isBearish(item)) return 'Ведмежий'
  return 'Нейтральний'
}

const cardBg = (item: any) => {
  if (isBullish(item)) return 'bg-green-950/40'
  if (isBearish(item)) return 'bg-red-950/40'
  return 'bg-gray-800/40'
}

const sentimentColor = (item: any) => {
  if (isBullish(item)) return 'text-green-400'
  if (isBearish(item)) return 'text-red-400'
  return 'text-gray-400'
}

const sentimentBadge = (item: any) => {
  if (isBullish(item)) return 'bg-green-900 text-green-300'
  if (isBearish(item)) return 'bg-red-900 text-red-300'
  return 'bg-gray-700 text-gray-400'
}

const wowColor = (item: any) => {
  if (item.net_change_wow == null) return 'text-gray-500'
  return item.net_change_wow >= 0 ? 'text-green-400' : 'text-red-400'
}

const wowArrow = (item: any) => {
  if (item.net_change_wow == null) return ''
  return item.net_change_wow >= 0 ? '▲' : '▼'
}
</script>
