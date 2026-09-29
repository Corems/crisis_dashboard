<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <!-- Header -->
    <div class="flex items-start justify-between mb-4">
      <div>
        <h2 class="text-lg font-semibold text-gray-100">AI Макро Аналіз</h2>
        <p v-if="analysis" class="text-xs text-gray-500 mt-0.5">
          {{ formatDate(analysis.generated_at) }}
          <span v-if="analysis.cached" class="ml-2 px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">кеш</span>
        </p>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="analysis" class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide" :class="riskClass(analysis.risk_level)">
          {{ riskLabel(analysis.risk_level) }}
        </span>
        <!-- Кнопка показується тільки якщо аналіз старший за 24 години -->
        <button
          v-if="canRegenerate"
          class="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors disabled:opacity-50 flex items-center gap-1.5"
          :disabled="generating"
          @click="doGenerate"
        >
          <span v-if="generating" class="inline-block w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
          {{ generating ? 'Генерую…' : 'Оновити аналіз' }}
        </button>
        <span v-else-if="analysis" class="text-xs text-gray-600">
          Оновлення через {{ hoursUntilRefresh }} год.
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-32 text-gray-500 text-sm">
      Завантаження аналізу…
    </div>

    <!-- Error -->
    <div v-else-if="fetchError && !analysis" class="flex items-center justify-center h-24 text-gray-500 text-sm">
      Аналіз ще не згенеровано. Натисніть «Оновити аналіз».
    </div>

    <!-- Content -->
    <template v-else-if="analysis">
      <!-- Risk explanation -->
      <p class="text-sm text-gray-400 mb-4 italic">{{ analysis.risk_explanation }}</p>

      <!-- Situation -->
      <div class="mb-4">
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Поточна ситуація</h3>
        <p class="text-sm text-gray-200 leading-relaxed">{{ analysis.situation }}</p>
      </div>

      <!-- Whales -->
      <div class="mb-4">
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Куди йдуть гроші</h3>
        <p class="text-sm text-gray-200 leading-relaxed">{{ analysis.whales }}</p>
      </div>

      <!-- Signals -->
      <div v-if="analysis.signals?.length" class="mb-4">
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Ключові сигнали</h3>
        <ul class="space-y-1">
          <li
            v-for="(signal, i) in analysis.signals"
            :key="i"
            class="flex gap-2 text-sm text-gray-300"
          >
            <span class="text-yellow-500 mt-0.5 shrink-0">•</span>
            {{ signal }}
          </li>
        </ul>
      </div>

      <!-- Investor action -->
      <div class="border-t border-gray-800 pt-4">
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Для роздрібного інвестора</h3>
        <p class="text-sm text-gray-200 leading-relaxed">{{ analysis.investor_action }}</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
const { getLatestAnalysis, generateAnalysis } = useApi()

const { data: analysis, error: fetchError, pending: loading, refresh } = await useAsyncData(
  'ai-analysis',
  () => getLatestAnalysis() as Promise<any>,
  { default: () => null }
)

const generating = ref(false)
const selectedProvider = ref('anthropic')

const REFRESH_HOURS = 24

const canRegenerate = computed(() => {
  if (!analysis.value?.generated_at) return true
  const age = Date.now() - new Date(analysis.value.generated_at).getTime()
  return age > REFRESH_HOURS * 60 * 60 * 1000
})

const hoursUntilRefresh = computed(() => {
  if (!analysis.value?.generated_at) return 0
  const age = Date.now() - new Date(analysis.value.generated_at).getTime()
  const remaining = REFRESH_HOURS * 60 * 60 * 1000 - age
  return Math.max(1, Math.ceil(remaining / (60 * 60 * 1000)))
})

const doGenerate = async () => {
  generating.value = true
  try {
    const result = await generateAnalysis(true, selectedProvider.value) as any
    analysis.value = result
  } catch (e: any) {
    const detail = e?.response?._data?.detail || e?.message || 'Помилка генерації'
    console.error('Failed to generate analysis', detail)
    alert(detail)
  } finally {
    generating.value = false
  }
}

const riskClass = (level: string) => {
  switch (level) {
    case 'low':      return 'bg-green-900 text-green-300'
    case 'moderate': return 'bg-yellow-900 text-yellow-300'
    case 'high':     return 'bg-orange-900 text-orange-300'
    case 'critical': return 'bg-red-900 text-red-300'
    default:         return 'bg-gray-800 text-gray-400'
  }
}

const riskLabel = (level: string) => {
  switch (level) {
    case 'low':      return 'Низький ризик'
    case 'moderate': return 'Помірний ризик'
    case 'high':     return 'Високий ризик'
    case 'critical': return 'Критичний ризик'
    default:         return level
  }
}

const formatDate = (d: string) =>
  new Date(d).toLocaleDateString('uk-UA', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
</script>
