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
            :stroke="gaugeColor"
            stroke-width="10"
            stroke-linecap="round"
            :stroke-dasharray="`${circumference}`"
            :stroke-dashoffset="dashOffset"
            style="transition: stroke-dashoffset 1s ease"
        />
      </svg>
      <!-- число всередині -->
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="text-4xl font-bold" :style="{ color: gaugeColor }">{{ Math.round(score) }}</span>
        <span class="text-gray-400 text-xs">/ 100</span>
      </div>
    </div>

    <!-- Текст -->
    <div>
      <div class="text-2xl font-semibold mb-1" :style="{ color: gaugeColor }">{{ label }}</div>
      <div class="text-gray-400 text-sm mb-1">CNN Fear & Greed Index</div>
      <div v-if="fetchedAt" class="text-gray-500 text-xs mb-3">
        Оновлено: {{ formatDateTime(fetchedAt) }}
      </div>

      <!-- Порівняння -->
      <div class="flex flex-col gap-1 text-xs text-gray-400">
        <div v-if="previousClose !== null" class="flex justify-between gap-4">
          <span>Попереднє закриття</span>
          <span :style="{ color: colorForScore(previousClose) }" class="font-medium">{{ Math.round(previousClose) }}</span>
        </div>
        <div v-if="oneWeekAgo !== null" class="flex justify-between gap-4">
          <span>Тиждень тому</span>
          <span :style="{ color: colorForScore(oneWeekAgo) }" class="font-medium">{{ Math.round(oneWeekAgo) }}</span>
        </div>
        <div v-if="oneMonthAgo !== null" class="flex justify-between gap-4">
          <span>Місяць тому</span>
          <span :style="{ color: colorForScore(oneMonthAgo) }" class="font-medium">{{ Math.round(oneMonthAgo) }}</span>
        </div>
      </div>

      <div class="mt-4 flex flex-wrap gap-2 text-xs">
        <span class="px-2 py-1 rounded-full bg-red-900 text-red-400">0–25 Екстр. страх</span>
        <span class="px-2 py-1 rounded-full bg-orange-900 text-orange-400">26–45 Страх</span>
        <span class="px-2 py-1 rounded-full bg-yellow-900 text-yellow-400">46–55 Нейтрально</span>
        <span class="px-2 py-1 rounded-full bg-lime-900 text-lime-400">56–75 Жадібність</span>
        <span class="px-2 py-1 rounded-full bg-green-900 text-green-400">76–100 Екстр. жадібність</span>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  score: number
  previousClose?: number | null
  oneWeekAgo?: number | null
  oneMonthAgo?: number | null
  fetchedAt?: string | null
}>()

const circumference = 2 * Math.PI * 42
const dashOffset = computed(() => circumference - (props.score / 100) * circumference)

function colorForScore(s: number): string {
  if (s <= 25) return '#ef4444'
  if (s <= 45) return '#f97316'
  if (s <= 55) return '#eab308'
  if (s <= 75) return '#84cc16'
  return '#22c55e'
}

const gaugeColor = computed(() => colorForScore(props.score))

const label = computed(() => {
  if (props.score <= 25) return 'Екстремальний страх'
  if (props.score <= 45) return 'Страх'
  if (props.score <= 55) return 'Нейтрально'
  if (props.score <= 75) return 'Жадібність'
  return 'Екстремальна жадібність'
})

const formatDateTime = (iso: string) => {
  const d = new Date(iso)
  return d.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit' }) + ', ' +
    d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
}
</script>
