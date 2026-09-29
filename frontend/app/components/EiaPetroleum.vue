<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <div class="flex items-start justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">Запаси нафтопродуктів США</h2>
        <p v-if="period" class="text-xs text-gray-500 mt-0.5">
          Тиждень {{ formatDate(period) }} · Щотижневий звіт EIA
        </p>
      </div>
      <span class="text-xs text-gray-600 mt-1">EIA</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-24 text-gray-500 text-sm">
      Завантаження даних EIA…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-24 text-red-400 text-sm">
      {{ error }}
    </div>

    <!-- Cards -->
    <div v-else-if="data.length" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div
        v-for="item in data"
        :key="item.product"
        class="rounded-xl p-4"
        :class="cardBg(item)"
      >
        <p class="text-xs font-medium mb-1" :class="labelColor(item)">
          {{ productLabel(item.product) }}
        </p>
        <p class="text-2xl font-bold text-white">
          {{ formatMbbl(item.value_mbbl) }}
          <span class="text-sm font-normal text-gray-400">Мбарр</span>
        </p>

        <!-- WoW change -->
        <p class="text-sm mt-2" :class="wowColor(item)">
          <span>{{ wowArrow(item) }}</span>
          {{ formatChange(item.wow_change) }} Мбарр
          <span class="text-gray-500 text-xs ml-1">({{ formatPct(item.wow_change_pct) }})</span>
        </p>

        <!-- vs 5yr avg -->
        <p v-if="item.five_year_avg != null" class="text-xs text-gray-500 mt-1">
          5-річне середнє: {{ formatMbbl(item.five_year_avg) }} Мбарр
          <span :class="vsAvgColor(item)">
            ({{ vsAvgLabel(item) }})
          </span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { getEiaPetroleum } = useApi()

const { data: rawData, error: fetchError, pending: loading } = await useAsyncData(
  'eia-petroleum',
  () => getEiaPetroleum() as Promise<any[]>
)

const data = computed(() => rawData.value ?? [])

const error = computed(() => {
  if (!fetchError.value) return null
  const status = (fetchError.value as any)?.response?.status
  if (status === 404) return 'Дані EIA ще не завантажено. Запустіть POST /api/collect/eia'
  return 'Помилка завантаження даних EIA'
})

const period = computed(() => data.value[0]?.period ?? null)

const PRODUCT_LABELS: Record<string, string> = {
  crude: 'Сира нафта',
  gasoline: 'Бензин',
  distillate: 'Дистиляти',
}

const productLabel = (p: string) => PRODUCT_LABELS[p] ?? p

const formatMbbl = (v: number) => v.toLocaleString('uk-UA', { maximumFractionDigits: 1 })
const formatDate = (d: string) =>
  new Date(d).toLocaleDateString('uk-UA', { year: 'numeric', month: 'long', day: 'numeric' })

const formatChange = (v: number | null) => {
  if (v == null) return '—'
  const abs = Math.abs(v).toLocaleString('uk-UA', { maximumFractionDigits: 1 })
  return (v >= 0 ? '+' : '−') + abs
}

const formatPct = (v: number | null) => {
  if (v == null) return '—'
  return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'
}

// Green when stocks are ABOVE 5yr avg (bearish for oil price), red when below
const aboveAvg = (item: any) =>
  item.five_year_avg != null && item.value_mbbl >= item.five_year_avg

const cardBg = (item: any) =>
  aboveAvg(item) ? 'bg-green-950/40' : 'bg-red-950/40'

const labelColor = (item: any) =>
  aboveAvg(item) ? 'text-green-400' : 'text-red-400'

const wowColor = (item: any) => {
  if (item.wow_change == null) return 'text-gray-400'
  return item.wow_change >= 0 ? 'text-green-400' : 'text-red-400'
}

const wowArrow = (item: any) => {
  if (item.wow_change == null) return ''
  return item.wow_change >= 0 ? '▲' : '▼'
}

const vsAvgColor = (item: any) =>
  aboveAvg(item) ? 'text-green-500' : 'text-red-500'

const vsAvgLabel = (item: any) => {
  if (item.five_year_avg == null) return ''
  const diff = item.value_mbbl - item.five_year_avg
  const pct = (diff / item.five_year_avg * 100).toFixed(1)
  return (diff >= 0 ? '+' : '') + pct + '%'
}
</script>
