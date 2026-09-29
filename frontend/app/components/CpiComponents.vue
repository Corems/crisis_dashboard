<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <div class="flex items-start justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">Компоненти інфляції (CPI)</h2>
        <p v-if="period" class="text-xs text-gray-500 mt-0.5">
          Дані за {{ formatPeriod(period) }} · BLS / FRED
        </p>
      </div>
      <span class="text-xs text-gray-600 mt-1">FRED</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-24 text-gray-500 text-sm">
      Завантаження даних CPI…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-24 text-red-400 text-sm">
      {{ error }}
    </div>

    <!-- Cards -->
    <div v-else-if="data.length" class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-4">
      <div
        v-for="item in data"
        :key="item.series_id"
        class="rounded-xl p-4"
        :class="cardBg(item)"
      >
        <p class="text-xs font-medium mb-2 leading-tight" :class="labelColor(item)">
          {{ shortName(item.name) }}
        </p>

        <!-- YoY -->
        <p class="text-2xl font-bold" :class="yoyColor(item)">
          {{ formatPct(item.yoy_change_pct) }}
        </p>
        <p class="text-xs text-gray-500 mb-2">рік до року</p>

        <!-- MoM -->
        <p class="text-sm" :class="momColor(item)">
          <span>{{ momArrow(item) }}</span>
          {{ formatPct(item.mom_change_pct) }}
          <span class="text-gray-600 text-xs ml-1">місяць до місяця</span>
        </p>

        <!-- Inflation badge -->
        <span
          class="inline-block mt-2 text-xs font-semibold px-2 py-0.5 rounded"
          :class="badgeClass(item)"
        >
          {{ badgeLabel(item) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { getCpiLatest } = useApi()

const { data: rawData, error: fetchError, pending: loading } = await useAsyncData(
  'cpi-latest',
  () => getCpiLatest() as Promise<any[]>
)

const data = computed(() => rawData.value ?? [])

const error = computed(() => {
  if (!fetchError.value) return null
  const status = (fetchError.value as any)?.response?.status
  if (status === 404) return 'Дані CPI ще не завантажено. Запустіть POST /api/collect/cpi'
  return 'Помилка завантаження даних CPI'
})

const period = computed(() => data.value[0]?.period ?? null)

const formatPeriod = (d: string) =>
  new Date(d).toLocaleDateString('uk-UA', { year: 'numeric', month: 'long' })

const formatPct = (v: number | null) => {
  if (v == null) return '—'
  return (v >= 0 ? '+' : '') + v.toFixed(2) + '%'
}

// Strip "CPI: " prefix for a compact card label
const shortName = (name: string) => name.replace(/^CPI:\s*/i, '')

// Thresholds: > 4% red, 2–4% yellow, < 2% green
const isHigh   = (item: any) => item.yoy_change_pct != null && item.yoy_change_pct > 4
const isMedium = (item: any) => item.yoy_change_pct != null && item.yoy_change_pct >= 2 && item.yoy_change_pct <= 4
const isLow    = (item: any) => item.yoy_change_pct != null && item.yoy_change_pct < 2

const cardBg = (item: any) => {
  if (isHigh(item))   return 'bg-red-950/40'
  if (isMedium(item)) return 'bg-yellow-950/40'
  if (isLow(item))    return 'bg-green-950/40'
  return 'bg-gray-800/40'
}

const labelColor = (item: any) => {
  if (isHigh(item))   return 'text-red-400'
  if (isMedium(item)) return 'text-yellow-400'
  if (isLow(item))    return 'text-green-400'
  return 'text-gray-400'
}

const yoyColor = (item: any) => {
  if (isHigh(item))   return 'text-red-400'
  if (isMedium(item)) return 'text-yellow-400'
  if (isLow(item))    return 'text-green-400'
  return 'text-white'
}

const momColor = (item: any) => {
  if (item.mom_change_pct == null) return 'text-gray-500'
  return item.mom_change_pct > 0 ? 'text-red-400' : 'text-green-400'
}

const momArrow = (item: any) => {
  if (item.mom_change_pct == null) return ''
  return item.mom_change_pct > 0 ? '▲' : '▼'
}

const badgeLabel = (item: any) => {
  if (isHigh(item))   return 'Висока'
  if (isMedium(item)) return 'Помірна'
  if (isLow(item))    return 'Низька'
  return '—'
}

const badgeClass = (item: any) => {
  if (isHigh(item))   return 'bg-red-900 text-red-300'
  if (isMedium(item)) return 'bg-yellow-900 text-yellow-300'
  if (isLow(item))    return 'bg-green-900 text-green-300'
  return 'bg-gray-700 text-gray-400'
}
</script>
