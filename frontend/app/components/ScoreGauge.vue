<template>
  <div class="bg-gray-900 rounded-2xl p-8 flex items-center gap-8">

    <!-- Кільце -->
    <div class="relative w-40 h-40 shrink-0">
      <svg viewBox="0 0 100 100" class="w-full h-full -rotate-90">
        <!-- фон -->
        <circle cx="50" cy="50" r="42" fill="none" stroke="#1f2937" stroke-width="10"/>
        <!-- прогрес -->
        <circle
            cx="50" cy="50" r="42"
            fill="none"
            :stroke="scoreColor"
            stroke-width="10"
            stroke-linecap="round"
            :stroke-dasharray="`${circumference}`"
            :stroke-dashoffset="dashOffset"
            style="transition: stroke-dashoffset 1s ease"
        />
      </svg>
      <!-- число всередині -->
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="text-4xl font-bold" :style="{ color: scoreColor }">{{ Math.round(score) }}</span>
        <span class="text-gray-400 text-xs">/ 100</span>
      </div>
    </div>

    <!-- Текст -->
    <div>
      <div class="text-2xl font-semibold mb-1" :style="{ color: scoreColor }">{{ label }}</div>
      <div class="text-gray-400 text-sm max-w-xs">
        Composite macroeconomic stress index based on {{ count }} indicators
      </div>
      <div v-if="lastUpdated" class="text-gray-500 text-xs mt-1">
        Оновлено: {{ formatDate(lastUpdated) }}
      </div>
      <div class="mt-4 flex gap-3 text-xs">
        <span class="px-2 py-1 rounded-full bg-green-900 text-green-400">0–33 Low</span>
        <span class="px-2 py-1 rounded-full bg-yellow-900 text-yellow-400">34–66 Medium</span>
        <span class="px-2 py-1 rounded-full bg-red-900 text-red-400">67–100 High</span>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  score: number
  count?: number
  lastUpdated?: string | null
}>()

const circumference = 2 * Math.PI * 42
const dashOffset = computed(() => circumference - (props.score / 100) * circumference)

const scoreColor = computed(() => {
  if (props.score < 34) return '#22c55e'
  if (props.score < 67) return '#eab308'
  return '#ef4444'
})

const label = computed(() => {
  if (props.score < 34) return 'Low Risk'
  if (props.score < 67) return 'Medium Risk'
  return 'High Risk'
})

const formatDate = (d: string) =>
  new Date(d).toLocaleDateString('uk-UA', { day: 'numeric', month: 'long', year: 'numeric' })
</script>
