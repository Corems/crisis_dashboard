<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <h2 class="text-lg font-semibold text-gray-100 mb-4">AI Чат (LongCat)</h2>

    <!-- Messages -->
    <div ref="messagesContainer" class="space-y-3 max-h-96 overflow-y-auto mb-4 pr-1">
      <div v-if="!messages.length" class="text-gray-500 text-sm text-center py-8">
        Задайте питання про макроекономіку, ринки або індикатори дашборду.
      </div>
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="flex"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed"
          :class="msg.role === 'user'
            ? 'bg-blue-900/60 text-blue-100'
            : 'bg-gray-800 text-gray-200'"
        >
          <div class="whitespace-pre-wrap">{{ msg.content }}</div>
        </div>
      </div>
      <div v-if="loading" class="flex justify-start">
        <div class="bg-gray-800 rounded-xl px-4 py-2.5 text-sm text-gray-400">
          <span class="inline-block w-2 h-2 bg-gray-400 rounded-full animate-bounce mr-1" />
          <span class="inline-block w-2 h-2 bg-gray-400 rounded-full animate-bounce mr-1" style="animation-delay: 0.15s" />
          <span class="inline-block w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.3s" />
        </div>
      </div>
    </div>

    <!-- Token usage -->
    <div v-if="lastUsage" class="text-[10px] text-gray-600 mb-2">
      Tokens: {{ lastUsage.input_tokens }} in / {{ lastUsage.output_tokens }} out
    </div>

    <!-- Input -->
    <form @submit.prevent="send" class="flex gap-2">
      <input
        v-model="input"
        type="text"
        placeholder="Ваше питання..."
        class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gray-500"
        :disabled="loading"
      />
      <button
        type="submit"
        :disabled="loading || !input.trim()"
        class="px-4 py-2.5 bg-blue-700 hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-white transition-colors"
      >
        Надіслати
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
const { sendChat } = useApi()

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])
const input = ref('')
const loading = ref(false)
const lastUsage = ref<{ input_tokens: number; output_tokens: number } | null>(null)
const messagesContainer = ref<HTMLElement | null>(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const send = async () => {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const resp = await sendChat(
      messages.value.map(m => ({ role: m.role, content: m.content }))
    ) as any
    messages.value.push({ role: 'assistant', content: resp.content })
    lastUsage.value = { input_tokens: resp.input_tokens, output_tokens: resp.output_tokens }
  } catch (e: any) {
    const detail = e?.response?._data?.detail || e?.message || 'Помилка запиту'
    messages.value.push({ role: 'assistant', content: `Помилка: ${detail}` })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>
