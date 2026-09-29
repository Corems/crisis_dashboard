<template>
  <div
    v-if="visible"
    class="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-4 py-3 bg-gray-800 border border-gray-600 rounded-xl shadow-lg text-sm text-white"
  >
    <span>📲 Встановити додаток</span>
    <button
      class="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors"
      @click="install"
    >
      Встановити
    </button>
    <button
      class="text-gray-400 hover:text-white transition-colors"
      @click="dismiss"
      aria-label="Закрити"
    >
      ✕
    </button>
  </div>
</template>

<script setup lang="ts">
const visible = ref(false)
let deferredPrompt: any = null

onMounted(() => {
  window.addEventListener('beforeinstallprompt', (e: Event) => {
    e.preventDefault()
    deferredPrompt = e
    visible.value = true
  })
})

async function install() {
  if (!deferredPrompt) return
  deferredPrompt.prompt()
  const { outcome } = await deferredPrompt.userChoice
  deferredPrompt = null
  visible.value = false
}

function dismiss() {
  visible.value = false
}
</script>
