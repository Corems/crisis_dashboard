export const useApi = () => {
    const baseUrl = '/api'

    const getIndicators = () =>
        $fetch(`${baseUrl}/indicators`)

    const getNews = (limit = 20) =>
        $fetch(`${baseUrl}/news?limit=${limit}`)

    const analyzeYoutube = (transcript: string) =>
        $fetch(`${baseUrl}/youtube/analyze`, {
            method: 'POST',
            body: { transcript }
        })

    const getBuffettHoldings = () =>
        $fetch(`${baseUrl}/buffett/holdings`)

    const getEiaPetroleum = () =>
        $fetch(`${baseUrl}/eia/petroleum`)

    const getManagersHoldings = () =>
        $fetch(`${baseUrl}/managers/holdings`)

    const getManagerHoldings = (key: string) =>
        $fetch(`${baseUrl}/managers/holdings/${key}`)

    const getFedBalance = () =>
        $fetch(`${baseUrl}/fed/balance`)

    const getCpiLatest = () =>
        $fetch(`${baseUrl}/cpi/latest`)

    const getCotLatest = () =>
        $fetch(`${baseUrl}/cot/latest`)

    const getCotHistory = (instrument: string, weeks = 52) =>
        $fetch(`${baseUrl}/cot/history?instrument=${instrument}&weeks=${weeks}`)

    const getLatestAnalysis = () =>
        $fetch(`${baseUrl}/analysis/latest`)

    const generateAnalysis = (force = false, provider?: string, model?: string) => {
        const params = new URLSearchParams({ force: String(force) })
        if (provider) params.set('provider', provider)
        if (model) params.set('model', model)
        return $fetch(`${baseUrl}/analysis/generate?${params}`, { method: 'POST' })
    }

    const getFearGreed = () =>
        $fetch(`${baseUrl}/fear-greed/latest`)

    const getIndexComparison = () =>
        $fetch(`${baseUrl}/indices/comparison`)

    const getMarketSignals = () =>
        $fetch(`${baseUrl}/signals/latest`)

    const sendChat = (messages: Array<{ role: string; content: string }>, model = 'LongCat-Flash-Chat', max_tokens = 2048) =>
        $fetch(`${baseUrl}/chat`, {
            method: 'POST',
            body: { messages, model, max_tokens }
        })

    return { getIndicators, getNews, analyzeYoutube, getBuffettHoldings, getManagersHoldings, getManagerHoldings, getEiaPetroleum, getFedBalance, getCpiLatest, getCotLatest, getCotHistory, getLatestAnalysis, generateAnalysis, getFearGreed, getIndexComparison, getMarketSignals, sendChat }
}
