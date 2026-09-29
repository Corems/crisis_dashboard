<template>
  <div class="min-h-screen bg-gray-950 text-white p-6">
    <PwaInstall />

    <header class="mb-8 flex items-start justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Crisis Dashboard</h1>
        <p class="text-gray-400 text-sm mt-1">Macroeconomic stress monitor</p>
      </div>
      <!-- Fear & Greed prominent display (top-right) -->
      <div v-if="fearGreed" class="shrink-0 text-right">
        <div class="text-xs text-gray-400 mb-1">Fear & Greed</div>
        <div class="text-2xl font-bold" :style="{ color: fgColor }">
          {{ Math.round((fearGreed as any).score) }} — {{ fgLabel }}
        </div>
        <div class="text-xs text-gray-500 mt-0.5" v-if="(fearGreed as any).fetched_at">
          {{ formatFgDate((fearGreed as any).fetched_at) }}
        </div>
      </div>
    </header>

    <section class="mb-8">
      <AiAnalysis />
    </section>

    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <ScoreGauge
        :score="indicators?.total_score ?? 0"
        :count="indicators?.indicators?.length"
        :last-updated="maxIndicatorDate"
      />
      <FearGreedGauge
        v-if="fearGreed"
        :score="(fearGreed as any).score"
        :previous-close="(fearGreed as any).previous_close"
        :one-week-ago="(fearGreed as any).one_week_ago"
        :one-month-ago="(fearGreed as any).one_month_ago"
        :fetched-at="(fearGreed as any).fetched_at"
      />
    </section>

    <section class="mb-8">
      <EntrySignals />
    </section>

    <section class="mb-8">
      <IndexComparison />
    </section>

    <section class="mb-8">
      <DrawdownTracker />
    </section>

    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <IndicatorsTable :indicators="indicators?.indicators ?? []" />
      <NewsFeed :items="news ?? []" />
    </section>

    <section class="mb-8">
      <FedBalance />
    </section>

    <section class="mb-8">
      <CpiComponents />
    </section>

    <section class="mb-8">
      <EiaPetroleum />
    </section>

    <section class="mb-8">
      <CotReport />
    </section>

    <section class="mb-8">
      <ManagersTracker />
    </section>

    <section class="mb-8">
      <BuffettTracker />
    </section>

    <section class="mb-8">
      <DcaCalculator />
    </section>

    <section class="mb-8">
      <TaxCalculator />
    </section>

    <section class="mb-8">
      <YouTubeAnalyzer />
    </section>

    <section class="mb-8">
      <StockAnalyzer />
    </section>

    <section class="mb-8">
      <LongCatChat />
    </section>

    <footer class="text-xs text-gray-600 text-center mt-8">
      Data collected daily from official sources. Each indicator is weighted 0–15 based on recession risk contribution. Max score 100 — higher means more economic stress.
    </footer>

  </div>
</template>

<script setup lang="ts">
import StockAnalyzer from "../components/StockAnalyzer.vue";

const { getIndicators, getNews, getFearGreed } = useApi()

const { data: indicators } = await useAsyncData(
  'indicators',
  () => getIndicators()
)

const { data: news } = await useAsyncData(
  'news',
  () => getNews(30)
)

const { data: fearGreed } = await useAsyncData(
  'fear-greed',
  () => getFearGreed().catch(() => null)
)

// Max indicator date for ScoreGauge
const maxIndicatorDate = computed(() => {
  const inds = (indicators.value as any)?.indicators
  if (!inds?.length) return null
  const dates = inds.map((i: any) => i.date).filter(Boolean)
  if (!dates.length) return null
  dates.sort()
  return dates[dates.length - 1]
})

// Fear & Greed header display
function fgColorForScore(s: number): string {
  if (s <= 24) return '#ef4444'
  if (s <= 44) return '#f97316'
  if (s <= 55) return '#eab308'
  if (s <= 74) return '#84cc16'
  return '#22c55e'
}

const fgColor = computed(() => {
  const fg = fearGreed.value as any
  return fg ? fgColorForScore(fg.score) : '#9ca3af'
})

const fgLabel = computed(() => {
  const fg = fearGreed.value as any
  if (!fg) return ''
  const s = fg.score
  if (s <= 24) return 'Extreme Fear'
  if (s <= 44) return 'Fear'
  if (s <= 55) return 'Neutral'
  if (s <= 74) return 'Greed'
  return 'Extreme Greed'
})

const formatFgDate = (iso: string) => {
  const d = new Date(iso)
  return d.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit' }) + ', ' +
    d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
}
</script>
