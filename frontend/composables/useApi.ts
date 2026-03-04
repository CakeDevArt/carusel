export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase as string

  async function request<T = any>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${baseURL}${path}`
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    }
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }
    const resp = await fetch(url, { ...options, headers })
    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(`API ${resp.status}: ${text}`)
    }
    if (resp.status === 204) return undefined as T
    return resp.json()
  }

  return {
    get: <T = any>(path: string) => request<T>(path),
    post: <T = any>(path: string, body?: any) =>
      request<T>(path, {
        method: 'POST',
        body: body instanceof FormData ? body : JSON.stringify(body),
      }),
    patch: <T = any>(path: string, body?: any) =>
      request<T>(path, {
        method: 'PATCH',
        body: JSON.stringify(body),
      }),
    del: (path: string) =>
      request(path, { method: 'DELETE' }),
    upload: <T = any>(path: string, formData: FormData) =>
      request<T>(path, {
        method: 'POST',
        body: formData,
      }),
    baseURL,
  }
}
