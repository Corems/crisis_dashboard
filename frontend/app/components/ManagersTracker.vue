<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <!-- Header -->
    <div class="flex items-start justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">Портфелі великих фондів (13F)</h2>
        <p v-if="activeData" class="text-xs text-gray-500 mt-0.5">
          Звіт за {{ formatQuarter(activeData.period_of_report) }} ·
          подано {{ formatDate(activeData.filing_date) }} ·
          портфель ${{ formatBillions(activeData.total_value_usd) }}
        </p>
      </div>
      <span class="text-xs text-gray-600 mt-1">SEC EDGAR</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-32 text-gray-500 text-sm">
      Завантаження даних EDGAR…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center h-24 text-red-400 text-sm">
      {{ error }}
    </div>

    <template v-else-if="data.length">
      <!-- Tab switcher -->
      <div class="flex gap-2 mb-4 border-b border-gray-800 pb-2">
        <button
          v-for="m in data"
          :key="m.manager_key"
          class="px-3 py-1 rounded-t text-sm font-medium transition-colors"
          :class="activeKey === m.manager_key
            ? 'bg-gray-700 text-white'
            : 'text-gray-500 hover:text-gray-300'"
          @click="activeKey = m.manager_key"
        >
          {{ managerLabel(m.manager_key) }}
        </button>
      </div>

      <!-- Holdings table -->
      <div v-if="activeData" class="overflow-auto max-h-96">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-gray-400 border-b border-gray-800">
              <th class="text-left pb-2">Компанія</th>
              <th class="text-right pb-2">Вартість</th>
              <th class="text-right pb-2">Частка</th>
              <th class="text-right pb-2">Зміна</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="h in activeData.holdings"
              :key="h.company_name"
              class="border-b border-gray-800/50 hover:bg-gray-800/30"
            >
              <td class="py-2 text-gray-300">
                <span class="font-mono text-xs text-gray-500 mr-2">{{ h.ticker }}</span>
                <span class="text-gray-200">{{ titleCase(h.company_name) }}</span>
              </td>
              <td class="py-2 text-right font-mono text-white">
                ${{ formatBillions(h.value_usd) }}
              </td>
              <td class="py-2 text-right font-mono text-gray-300">
                {{ h.portfolio_pct.toFixed(1) }}%
              </td>
              <td class="py-2 text-right">
                <span
                  class="px-2 py-0.5 rounded text-xs font-semibold"
                  :class="changeClass(h.change_type)"
                >
                  {{ changeLabel(h.change_type, h.change_pct) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
const { getManagersHoldings } = useApi()

const { data: rawData, error: fetchError, pending: loading } = await useAsyncData(
  'managers-holdings',
  () => getManagersHoldings() as Promise<any[]>
)

const data = computed(() => rawData.value ?? [])

const error = computed(() => {
  if (!fetchError.value) return null
  const status = (fetchError.value as any)?.response?.status
  if (status === 404) return 'Дані 13F ще не завантажено. Запустіть POST /api/collect/managers_13f'
  return 'Помилка завантаження даних EDGAR'
})

const activeKey = ref<string>('')

// Set default tab once data loads
watch(data, (val) => {
  if (val.length && !activeKey.value) {
    activeKey.value = val[0].manager_key
  }
}, { immediate: true })

const activeData = computed(() =>
  data.value.find((m: any) => m.manager_key === activeKey.value) ?? null
)

const MANAGER_LABELS: Record<string, string> = {
  bridgewater: 'Bridgewater',
  scion:       'Scion',
  pershing:    'Pershing Sq.',
}

const managerLabel = (k: string) => MANAGER_LABELS[k] ?? k

const formatDate = (d: string) =>
  new Date(d).toLocaleDateString('uk-UA', { year: 'numeric', month: 'long', day: 'numeric' })

const formatQuarter = (period: string) => {
  if (!period) return ''
  const d = new Date(period)
  const q = Math.ceil((d.getMonth() + 1) / 3)
  return `Q${q} ${d.getFullYear()}`
}

const formatBillions = (usd: number) => {
  if (usd >= 1e12) return (usd / 1e12).toFixed(2) + 'T'
  if (usd >= 1e9)  return (usd / 1e9).toFixed(1) + 'B'
  if (usd >= 1e6)  return (usd / 1e6).toFixed(0) + 'M'
  return usd.toFixed(0)
}

const titleCase = (s: string) =>
  s.toLowerCase().replace(/\b\w/g, c => c.toUpperCase())

const changeClass = (type: string) => {
  switch (type) {
    case 'new':       return 'bg-blue-900 text-blue-300'
    case 'increased': return 'bg-green-900 text-green-300'
    case 'decreased': return 'bg-red-900 text-red-300'
    case 'exited':    return 'bg-red-950 text-red-400'
    default:          return 'bg-gray-800 text-gray-500'
  }
}

const changeLabel = (type: string, pct: number | null) => {
  switch (type) {
    case 'new':       return '🆕 Нова'
    case 'increased': return pct != null ? `▲ ${pct > 0 ? '+' : ''}${pct}%` : '▲'
    case 'decreased': return pct != null ? `▼ ${pct}%` : '▼'
    case 'exited':    return '✕ Вихід'
    default:          return '—'
  }
}
</script>
