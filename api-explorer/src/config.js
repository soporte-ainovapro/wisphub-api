// Base URL — uses Vite proxy in dev, direct URL in prod
export const BASE_URL = ''

const METHOD_COLORS = {
    GET: 'text-emerald-400',
    POST: 'text-blue-400',
    PUT: 'text-amber-400',
    DELETE: 'text-red-400',
}

export { METHOD_COLORS }

export async function apiRequest(method, path, body = null) {
    const start = performance.now()
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
    }
    if (body) options.body = JSON.stringify(body)

    const response = await fetch(BASE_URL + path, options)
    const elapsed = Math.round(performance.now() - start)
    let data
    try {
        data = await response.json()
    } catch {
        data = null
    }
    return { status: response.status, data, elapsed }
}
