<template>
  <div class="bg-gray-900 rounded-2xl p-6">

    <div class="mb-5">
      <h2 class="text-lg font-semibold text-gray-100">DCA Калькулятор</h2>
      <p class="text-xs text-gray-500 mt-0.5">Регулярні інвестиції в S&amp;P 500</p>
    </div>

    <!-- Sliders -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-6">

      <div>
        <div class="flex justify-between text-xs text-gray-400 mb-2">
          <span>Щомісячна сума</span>
          <span class="text-white font-semibold">${{ monthly }}</span>
        </div>
        <input
          v-model.number="monthly"
          type="range" min="100" max="2000" step="50"
          class="w-full accent-blue-500 cursor-pointer"
        />
        <div class="flex justify-between text-xs text-gray-600 mt-1">
          <span>$100</span><span>$2 000</span>
        </div>
      </div>

      <div>
        <div class="flex justify-between text-xs text-gray-400 mb-2">
          <span>Горизонт</span>
          <span class="text-white font-semibold">{{ horizon }} р.</span>
        </div>
        <input
          v-model.number="horizon"
          type="range" min="1" max="30" step="1"
          class="w-full accent-blue-500 cursor-pointer"
        />
        <div class="flex justify-between text-xs text-gray-600 mt-1">
          <span>1 р.</span><span>30 р.</span>
        </div>
      </div>

      <div>
        <div class="flex justify-between text-xs text-gray-400 mb-2">
          <span>Річна дохідність</span>
          <span class="text-white font-semibold">{{ rate }}%</span>
        </div>
        <input
          v-model.number="rate"
          type="range" min="5" max="15" step="0.5"
          class="w-full accent-blue-500 cursor-pointer"
        />
        <div class="flex justify-between text-xs text-gray-600 mt-1">
          <span>5%</span><span>15%</span>
        </div>
      </div>

    </div>

    <!-- SVG Chart -->
    <div class="mb-5">
      <div class="flex gap-5 mb-3 text-xs text-gray-400">
        <span class="flex items-center gap-1.5">
          <span class="w-6 h-0.5 inline-block bg-blue-500 rounded"></span>
          Портфель DCA
        </span>
        <span class="flex items-center gap-1.5">
          <span class="w-6 h-px inline-block bg-gray-500" style="border-top: 1px dashed #6b7280;"></span>
          Внески
        </span>
      </div>

      <svg viewBox="0 0 400 140" class="w-full" style="height: 170px;" preserveAspectRatio="none">
        <!-- Y grid lines -->
        <line v-for="(gl, i) in yGridLines" :key="i"
          :x1="PAD_L" :y1="gl.y" :x2="400 - PAD_R" :y2="gl.y"
          stroke="#1f2937" stroke-width="0.8"
        />
        <!-- Y labels -->
        <text v-for="(gl, i) in yGridLines" :key="'yl'+i"
          :x="PAD_L - 4" :y="gl.y + 3"
          text-anchor="end" font-size="8" fill="#6b7280"
        >{{ gl.label }}</text>

        <!-- Contributions dashed line -->
        <polyline
          :points="contributionPoints"
          fill="none"
          stroke="#6b7280"
          stroke-width="1.2"
          stroke-dasharray="4,3"
        />

        <!-- Portfolio filled area (subtle) -->
        <polygon
          :points="portfolioFill"
          fill="#3b82f6"
          fill-opacity="0.08"
        />

        <!-- Portfolio line -->
        <polyline
          :points="portfolioPoints"
          fill="none"
          stroke="#3b82f6"
          stroke-width="2"
          stroke-linejoin="round"
          stroke-linecap="round"
        />

        <!-- X axis labels -->
        <text :x="PAD_L" :y="140 - 2" font-size="8" fill="#6b7280" text-anchor="middle">0</text>
        <text :x="400 - PAD_R" :y="140 - 2" font-size="8" fill="#6b7280" text-anchor="middle">{{ horizon }}р</text>
      </svg>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
      <div class="rounded-xl bg-gray-800/60 p-3">
        <p class="text-xs text-gray-500 mb-1">Внески</p>
        <p class="text-base font-bold text-white">{{ fmtMoney(totalContributions) }}</p>
      </div>
      <div class="rounded-xl bg-blue-950/50 p-3">
        <p class="text-xs text-gray-500 mb-1">DCA портфель</p>
        <p class="text-base font-bold text-blue-400">{{ fmtMoney(dcaFinalValue) }}</p>
      </div>
      <div class="rounded-xl bg-green-950/40 p-3">
        <p class="text-xs text-gray-500 mb-1">Прибуток</p>
        <p class="text-base font-bold text-green-400">{{ fmtMoney(profit) }}</p>
        <p class="text-xs text-green-600">+{{ profitPct.toFixed(0) }}%</p>
      </div>
      <div class="rounded-xl bg-yellow-950/40 p-3">
        <p class="text-xs text-gray-500 mb-1">Лампсам¹</p>
        <p class="text-base font-bold text-yellow-400">{{ fmtMoney(lumpSumValue) }}</p>
      </div>
    </div>

    <!-- Comparison row -->
    <div
      class="rounded-xl px-4 py-3 text-sm text-center"
      :class="lumpSumValue > dcaFinalValue ? 'bg-yellow-950/40' : 'bg-blue-950/40'"
    >
      <span :class="lumpSumValue > dcaFinalValue ? 'text-yellow-400' : 'text-blue-400'">
        {{ comparisonText }}
      </span>
    </div>

    <p class="text-xs text-gray-700 mt-3">
      ¹ Лампсам — всі майбутні внески ({{ fmtMoney(totalContributions) }}) вкладені одноразово сьогодні
    </p>

  </div>
</template>

<script setup lang="ts">
const monthly = ref(500)
const horizon = ref(10)
const rate = ref(10)

// Chart geometry
const PAD_L = 30
const PAD_R = 8
const PAD_T = 10
const PAD_B = 18
const CHART_W = 400 - PAD_L - PAD_R
const CHART_H = 140 - PAD_T - PAD_B

// DCA future value formula
function dcaFV(m: number, months: number, annualRate: number): number {
  if (months === 0) return 0
  const r = annualRate / 100 / 12
  if (r === 0) return m * months
  return m * ((Math.pow(1 + r, months) - 1) / r)
}

// Year-by-year data points
const chartPoints = computed(() => {
  const pts = []
  for (let y = 0; y <= horizon.value; y++) {
    pts.push({
      year: y,
      contributions: monthly.value * 12 * y,
      portfolio: dcaFV(monthly.value, y * 12, rate.value),
    })
  }
  return pts
})

const totalContributions = computed(() => monthly.value * 12 * horizon.value)
const dcaFinalValue = computed(() => dcaFV(monthly.value, horizon.value * 12, rate.value))
const lumpSumValue = computed(() => totalContributions.value * Math.pow(1 + rate.value / 100, horizon.value))
const profit = computed(() => dcaFinalValue.value - totalContributions.value)
const profitPct = computed(() => totalContributions.value > 0 ? profit.value / totalContributions.value * 100 : 0)

const comparisonText = computed(() => {
  const diff = Math.abs(lumpSumValue.value - dcaFinalValue.value)
  if (lumpSumValue.value > dcaFinalValue.value) {
    return `Лампсам вигідніший на ${fmtMoney(diff)} (але потребує всіх грошей одразу)`
  }
  return `DCA вигідніший на ${fmtMoney(diff)}`
})

// SVG helpers
const maxVal = computed(() => Math.max(dcaFinalValue.value, 1))

function svgX(year: number): number {
  return PAD_L + (year / horizon.value) * CHART_W
}
function svgY(val: number): number {
  return PAD_T + (1 - val / maxVal.value) * CHART_H
}

const portfolioPoints = computed(() =>
  chartPoints.value.map(p => `${svgX(p.year).toFixed(1)},${svgY(p.portfolio).toFixed(1)}`).join(' ')
)

const contributionPoints = computed(() =>
  chartPoints.value.map(p => `${svgX(p.year).toFixed(1)},${svgY(p.contributions).toFixed(1)}`).join(' ')
)

const portfolioFill = computed(() => {
  const pts = chartPoints.value
  if (pts.length === 0) return ''
  const line = pts.map(p => `${svgX(p.year).toFixed(1)},${svgY(p.portfolio).toFixed(1)}`).join(' ')
  const baseY = (PAD_T + CHART_H).toFixed(1)
  return `${PAD_L},${baseY} ${line} ${svgX(horizon.value).toFixed(1)},${baseY}`
})

// Y-axis grid lines (3 lines: 0, 50%, 100%)
const yGridLines = computed(() => {
  const max = maxVal.value
  return [0, 0.5, 1].map(ratio => ({
    y: svgY(max * ratio),
    label: fmtMoney(max * ratio, true),
  }))
})

function fmtMoney(v: number, short = false): string {
  if (short) {
    if (v >= 1_000_000) return '$' + (v / 1_000_000).toFixed(1) + 'M'
    if (v >= 1_000) return '$' + (v / 1_000).toFixed(0) + 'K'
    return '$' + v.toFixed(0)
  }
  if (v >= 1_000_000) return '$' + (v / 1_000_000).toFixed(2) + 'M'
  if (v >= 1_000) return '$' + v.toLocaleString('en-US', { maximumFractionDigits: 0 })
  return '$' + v.toFixed(0)
}
</script>
