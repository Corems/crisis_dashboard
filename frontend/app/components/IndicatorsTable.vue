<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <h2 class="text-lg font-semibold mb-4 text-gray-100">Indicators</h2>
    <div class="overflow-auto max-h-96">
      <table class="w-full text-sm">
        <thead>
        <tr class="text-gray-400 border-b border-gray-800">
          <th class="text-left pb-2">Name</th>
          <th class="text-right pb-2">Value</th>
          <th class="text-right pb-2">Delta</th>
          <th class="text-right pb-2">Score</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="ind in indicators" :key="ind.fred_id" class="border-b border-gray-800/50 hover:bg-gray-800/30">
          <td class="py-2 text-gray-300">
            <span
              class="cursor-help border-b border-dashed border-gray-600"
              @mouseenter="showHint(ind, $event)"
              @mouseleave="hideHint"
            >{{ind.fred_id}} - {{ ind.name }}</span>
          </td>
          <td class="py-2 text-right text-white font-mono">{{ formatValue(ind.value) }}</td>
          <td class="py-2 text-right font-mono" :class="deltaColor(ind.delta, ind.inverted)">
            {{ ind.delta != null ? (ind.delta > 0 ? '+' : '') + formatValue(ind.delta) : '—' }}
          </td>
          <td class="py-2 text-right">
            <span class="px-2 py-0.5 rounded text-xs font-bold" :class="scoreClass(ind.score, ind.weight)">
              {{ ind.score }}
            </span>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- Teleport рендерить tooltip прямо в <body> — поза будь-яким overflow -->
    <Teleport to="body">
      <div
        v-if="activeHint"
        :style="{ top: tooltipY + 'px', left: tooltipX + 'px' }"
        class="fixed z-[9999] w-80 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl p-4 text-xs pointer-events-none"
      >
        <div class="mb-2">
          <span class="text-gray-400 uppercase tracking-wide text-[10px]">Що це</span>
          <p class="text-gray-200 mt-1">{{ activeHint.what }}</p>
        </div>
        <div class="mb-2">
          <span class="text-gray-400 uppercase tracking-wide text-[10px]">Як читати</span>
          <p class="text-gray-200 mt-1">{{ activeHint.how }}</p>
        </div>
        <div class="mb-2">
          <span class="text-gray-400 uppercase tracking-wide text-[10px]">Вплив</span>
          <p class="text-gray-200 mt-1">{{ activeHint.impact }}</p>
        </div>
        <div v-if="activeHintDate || activeHintFetchedAt" class="border-t border-gray-700 pt-2">
          <p v-if="activeHintDate" class="text-gray-400 text-[10px]">
            Оновлено: <span class="text-gray-300">{{ activeHintDate }}</span>
          </p>
          <p v-if="activeHintFetchedAt" class="text-gray-400 text-[10px]">
            Отримано: <span class="text-gray-300">{{ formatDateTime(activeHintFetchedAt) }}</span>
          </p>
          <p v-if="activeHintFrequency" class="text-gray-400 text-[10px] mt-0.5">
            Частота: <span class="text-gray-300">{{ activeHintFrequency }}</span>
          </p>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  indicators: any[]
}>()

const activeHint = ref<{ what: string; how: string; impact: string } | null>(null)
const activeHintDate = ref<string | null>(null)
const activeHintFetchedAt = ref<string | null>(null)
const activeHintFrequency = ref<string | null>(null)
const tooltipX = ref(0)
const tooltipY = ref(0)

const showHint = (ind: any, event: MouseEvent) => {
  if (!ind.hint?.what) return
  activeHint.value = ind.hint
  activeHintDate.value = ind.date || null
  activeHintFetchedAt.value = ind.fetched_at || null
  activeHintFrequency.value = ind.update_frequency || null

  const rect = (event.target as HTMLElement).getBoundingClientRect()
  tooltipX.value = rect.left
  const spaceBelow = window.innerHeight - rect.bottom
  if (spaceBelow < 280) {
    tooltipY.value = rect.top - 280
  } else {
    tooltipY.value = rect.bottom + 6
  }
}

const hideHint = () => {
  activeHint.value = null
  activeHintDate.value = null
  activeHintFetchedAt.value = null
  activeHintFrequency.value = null
}

const formatValue = (v: number) => {
  if (Math.abs(v) >= 1000) return v.toLocaleString('en-US', { maximumFractionDigits: 0 })
  return v.toLocaleString('en-US', { maximumFractionDigits: 4 })
}

const formatDateTime = (iso: string) => {
  const d = new Date(iso)
  return d.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit' }) + ', ' +
    d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
}

const deltaColor = (delta: number | null, inverted: boolean = false) => {
  if (delta == null) return 'text-gray-500'
  const isGood = inverted ? delta > 0 : delta < 0
  return isGood ? 'text-green-400' : 'text-red-400'
}

const scoreClass = (score: number, weight: number) => {
  const ratio = score / weight
  if (ratio > 0.66) return 'bg-red-900 text-red-300'
  if (ratio > 0.33) return 'bg-yellow-900 text-yellow-300'
  return 'bg-green-900 text-green-300'
}
</script>
