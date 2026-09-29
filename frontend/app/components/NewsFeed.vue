<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <h2 class="text-lg font-semibold mb-4 text-gray-100">News Feed</h2>
    <div class="overflow-auto max-h-96 space-y-3">
    <div
        v-for="item in items"
        :key="item.id"
        @click="openLink(item.url)"
        class="block p-3 rounded-xl bg-gray-800/50 hover:bg-gray-800 transition-colors cursor-pointer"
    >
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-300">{{ item.source }}</span>
        <span class="text-xs text-gray-500">{{ formatDate(item.published_at) }}</span>
      </div>
      <p class="text-sm text-gray-200 leading-snug">{{ item.title }}</p>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  items: any[]
}>()

const formatDate = (d: string | null) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const openLink = (url: string) => window.open(url, '_blank')
</script>
