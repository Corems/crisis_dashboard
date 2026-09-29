<template>
  <div class="bg-gray-900 rounded-2xl p-6">
    <h2 class="text-lg font-semibold mb-4 text-gray-100">YouTube Transcript Analysis</h2>

    <div class="space-y-4">
      <!-- URL Input -->
      <div class="flex gap-2">
        <input
          v-model="youtubeUrl"
          type="text"
          placeholder="Paste YouTube URL here..."
          class="flex-1 px-4 py-2 bg-gray-800 rounded-lg text-gray-100 placeholder-gray-500 border border-gray-700 focus:border-blue-500 focus:outline-none"
          @keyup.enter="analyze"
          :disabled="loading"
        />
        <button
          @click="analyze"
          :disabled="loading || !youtubeUrl"
          class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
        >
          {{ loading ? (loadingMessage || 'Processing...') : 'Analyze' }}
        </button>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
        {{ error }}
      </div>

      <!-- Loading Indicator -->
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>

      <!-- Analysis Result -->
      <div v-if="result && !loading" class="space-y-4">
        <!-- Analysis -->
        <div class="p-4 bg-gray-800/50 rounded-xl">
          <h3 class="text-md font-semibold mb-3 text-gray-100">Analysis</h3>
          <div class="prose prose-invert prose-sm max-w-none text-gray-200" v-html="renderMarkdown(result.analysis)"></div>
        </div>

        <!-- Transcript Toggle -->
        <div class="border-t border-gray-800 pt-4">
          <button
            @click="showTranscript = !showTranscript"
            class="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
          >
            <svg
              class="w-4 h-4 transition-transform"
              :class="{ 'rotate-90': showTranscript }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            {{ showTranscript ? 'Hide' : 'Show' }} Transcript
          </button>

          <!-- Transcript Content -->
          <div v-if="showTranscript" class="mt-3 p-4 bg-gray-800/30 rounded-lg max-h-64 overflow-auto">
            <p class="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{{ result.transcript }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { marked } from 'marked'
import { Supadata } from '@supadata/js'

const { analyzeYoutube } = useApi()
const config = useRuntimeConfig()

const youtubeUrl = ref('')
const loading = ref(false)
const loadingMessage = ref('')
const error = ref('')
const result = ref<{ transcript: string; analysis: string } | null>(null)
const showTranscript = ref(false)

const renderMarkdown = (text: string) => {
  return marked(text)
}

const analyze = async () => {
  if (!youtubeUrl.value || loading.value) return

  loading.value = true
  error.value = ''
  result.value = null
  showTranscript.value = false

  try {
    // 1. Fetch transcript via Supadata SDK (client-side)
    loadingMessage.value = 'Fetching transcript...'

    const supadata = new Supadata({ apiKey: config.public.supadataApiKey as string })
    let transcriptResult = await supadata.youtube.transcript({ url: youtubeUrl.value, text: true, mode: 'auto' })

    // If async job, poll until completed
    if (transcriptResult.jobId) {
      while (true) {
        await new Promise(resolve => setTimeout(resolve, 3000))
        const status = await supadata.youtube.transcript.getJobStatus(transcriptResult.jobId)
        if (status.status === 'completed') {
          transcriptResult = status
          break
        }
        if (status.status === 'failed') {
          throw new Error('Transcript job failed')
        }
      }
    }

    const transcript = transcriptResult.content
    if (!transcript || transcript.trim().length === 0) {
      throw new Error('Empty transcript received')
    }

    // 2. Send transcript to backend for Claude analysis
    loadingMessage.value = 'Analyzing...'
    const data = await analyzeYoutube(transcript) as { transcript: string; analysis: string }
    result.value = data
  } catch (err: any) {
    error.value = err.data?.detail || err.message || 'Failed to analyze video'
  } finally {
    loading.value = false
    loadingMessage.value = ''
  }
}
</script>
