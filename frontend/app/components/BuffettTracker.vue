<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <div class="flex items-start justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">Портфель Баффета (13F)</h2>
        <p v-if="data" class="text-xs text-gray-500 mt-0.5">
          Звіт за {{ formatQuarter(data.period_of_report) }} · подано {{ formatDate(data.filing_date) }} ·
          портфель ${{ formatBillions(data.total_value_usd) }}
        </p>
        <p v-if="data" class="text-xs text-gray-600 mt-0.5">
          Наступний 13F очікується ~{{ nextFilingDate(data.period_of_report) }}
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

    <!-- Table -->
    <div v-else-if="data" class="overflow-auto max-h-96">
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
            v-for="h in data.holdings"
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
  </div>
</template>

<script setup lang="ts">
const { getBuffettHoldings } = useApi()

const { data, error: fetchError, pending: loading } = await useAsyncData(
  'buffett-holdings',
  () => getBuffettHoldings()
)

const error = computed(() => {
  if (!fetchError.value) return null
  const status = (fetchError.value as any)?.response?.status
  if (status === 404) return 'Дані 13F ще не завантажено. Запустіть POST /api/collect/buffett'
  return 'Помилка завантаження даних EDGAR'
})

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
  if (usd >= 1e9) return (usd / 1e9).toFixed(1) + 'B'
  if (usd >= 1e6) return (usd / 1e6).toFixed(0) + 'M'
  return usd.toFixed(0)
}

const nextFilingDate = (period: string) => {
  if (!period) return '?'

  const periodEnd = new Date(period)
  const month = periodEnd.getMonth()

  let nextQuarterEnd: Date
  if (month <= 2) {
    nextQuarterEnd = new Date(periodEnd.getFullYear(), 5, 30)
  } else if (month <= 5) {
    nextQuarterEnd = new Date(periodEnd.getFullYear(), 8, 30)
  } else if (month <= 8) {
    nextQuarterEnd = new Date(periodEnd.getFullYear(), 11, 31)
  } else {
    nextQuarterEnd = new Date(periodEnd.getFullYear() + 1, 2, 31)
  }

  // +45 днів від кінця наступного кварталу
  nextQuarterEnd.setDate(nextQuarterEnd.getDate() + 45)

  return nextQuarterEnd.toLocaleDateString('uk-UA', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
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
