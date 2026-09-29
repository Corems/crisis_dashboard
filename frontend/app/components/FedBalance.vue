<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <!-- Header -->
    <div class="flex items-start justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">Баланс Федерального Резерву (H.4.1)</h2>
        <p v-if="period" class="text-xs text-gray-500 mt-0.5">
          Тиждень {{ formatDate(period) }} · ФРС США
        </p>
      </div>
      <span class="text-xs text-gray-600 mt-1">FRED</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-24 text-gray-500 text-sm">
      Завантаження даних ФРС…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-24 text-red-400 text-sm">
      {{ error }}
    </div>

    <template v-else-if="data.length">
      <!-- Total Assets hero row -->
      <div
        v-if="totalAssets"
        class="rounded-xl p-4 mb-4"
        :class="heroBg(totalAssets)"
      >
        <div class="flex items-center justify-between flex-wrap gap-2">
          <div>
            <p class="text-xs font-medium text-gray-400 mb-1">Загальні активи ФРС</p>
            <p class="text-3xl font-bold text-white">
              {{ formatTrillions(totalAssets.value_bln) }}
              <span class="text-base font-normal text-gray-400">трлн $</span>
            </p>
          </div>
          <div class="text-right">
            <p class="text-sm" :class="wowColor(totalAssets)">
              {{ wowArrow(totalAssets) }} {{ formatBln(totalAssets.wow_change) }} тижн.
            </p>
            <p class="text-sm mt-1" :class="yoyColor(totalAssets)">
              {{ yoyArrow(totalAssets) }} {{ formatBln(totalAssets.yoy_change) }} рік
            </p>
          </div>
          <span
            class="text-xs font-bold px-3 py-1 rounded-full"
            :class="policyBadge(totalAssets)"
          >
            {{ policyLabel(totalAssets) }}
          </span>
        </div>
      </div>

      <!-- Component cards -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div
          v-for="item in componentItems"
          :key="item.series_id"
          class="rounded-xl p-3 bg-gray-800/50"
        >
          <p class="text-xs text-gray-400 leading-tight mb-2">{{ shortName(item.name) }}</p>
          <p class="text-lg font-bold text-white">
            {{ formatValue(item) }}
            <span class="text-xs font-normal text-gray-500">{{ unit(item) }}</span>
          </p>
          <p class="text-xs mt-1" :class="wowColor(item)">
            {{ wowArrow(item) }} {{ formatBln(item.wow_change) }}
            <span class="text-gray-600 ml-1">WoW</span>
          </p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
const { getFedBalance } = useApi()

const { data: rawData, error: fetchError, pending: loading } = await useAsyncData(
  'fed-balance',
  () => getFedBalance() as Promise<any[]>
)

const data = computed(() => rawData.value ?? [])

const error = computed(() => {
  if (!fetchError.value) return null
  const status = (fetchError.value as any)?.response?.status
  if (status === 404) return 'Дані ФРС ще не завантажено. Запустіть POST /api/collect/fed_balance'
  return 'Помилка завантаження даних ФРС'
})

const period = computed(() => data.value[0]?.period ?? null)

const totalAssets    = computed(() => data.value.find((r: any) => r.series_id === 'WALCL') ?? null)
const componentItems = computed(() =>
  data.value.filter((r: any) => ['WTREGEN', 'WMBSEC', 'RRPONTSYD', 'WLRRAL'].includes(r.series_id))
)

const formatDate = (d: string) =>
  new Date(d).toLocaleDateString('uk-UA', { year: 'numeric', month: 'long', day: 'numeric' })

const formatValue = (item: any) => {
  const mln = item.value_bln  // насправді мільйони
  if (mln >= 1_000_000) return (mln / 1_000_000).toFixed(2)  // трлн
  if (mln >= 1_000) return (mln / 1_000).toFixed(0)           // млрд
  return mln.toFixed(1)                                         // млн
}

const unit = (item: any) => {
  const mln = item.value_bln
  if (mln >= 1_000_000) return 'трлн $'
  if (mln >= 1_000) return 'млрд $'
  return 'млн $'
}

const formatTrillions = (mln: number) => (mln / 1_000_000).toFixed(2)

const formatBln = (v: number | null) => {
  if (v == null) return '—'
  const abs = Math.abs(v)
  const sign = v >= 0 ? '+' : '−'
  if (abs >= 1_000_000) return sign + (abs / 1_000_000).toFixed(2) + ' трлн $'
  if (abs >= 1_000) return sign + (abs / 1_000).toFixed(0) + ' млрд $'
  return sign + abs.toFixed(0) + ' млн $'
}

const shortName = (name: string) => name.replace(/^ФРС:\s*/i, '')

const isShrinking = (item: any) => item.wow_change != null && item.wow_change < 0
const isGrowing   = (item: any) => item.wow_change != null && item.wow_change > 0

const heroBg = (item: any) => {
  if (isShrinking(item)) return 'bg-green-950/40'
  if (isGrowing(item))   return 'bg-red-950/40'
  return 'bg-gray-800/40'
}

const wowColor = (item: any) => {
  if (item.wow_change == null) return 'text-gray-500'
  return item.wow_change < 0 ? 'text-green-400' : 'text-red-400'
}

const wowArrow = (item: any) => {
  if (item.wow_change == null) return ''
  return item.wow_change >= 0 ? '▲' : '▼'
}

const yoyColor = (item: any) => {
  if (item.yoy_change == null) return 'text-gray-500'
  return item.yoy_change < 0 ? 'text-green-400' : 'text-red-400'
}

const yoyArrow = (item: any) => {
  if (item.yoy_change == null) return ''
  return item.yoy_change >= 0 ? '▲' : '▼'
}

const policyLabel = (item: any) => {
  if (isShrinking(item)) return 'QT — Скорочення'
  if (isGrowing(item))   return 'QE — Розширення'
  return 'Без змін'
}

const policyBadge = (item: any) => {
  if (isShrinking(item)) return 'bg-green-900 text-green-300'
  if (isGrowing(item))   return 'bg-red-900 text-red-300'
  return 'bg-gray-700 text-gray-400'
}
</script>
