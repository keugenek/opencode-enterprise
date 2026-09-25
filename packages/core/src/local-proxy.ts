import { request } from "node:http"
import { Readable } from "node:stream"
import type { ModelsDev } from "./models-dev"

declare const OPENCODE_LOCAL_PROXY_ONLY: boolean | undefined

// Replaced by the build scripts. Runtime environment/config cannot turn this off.
export const enabled = typeof OPENCODE_LOCAL_PROXY_ONLY !== "undefined" && OPENCODE_LOCAL_PROXY_ONLY
export const id = "local-proxy"
export const baseURL = "http://localhost:8081/v1"

export function assertURL(input: string | URL) {
  const url = new URL(input)
  if (url.origin !== "http://localhost:8081" || url.username || url.password || !url.pathname.startsWith("/v1/")) {
    throw new Error("This build only supports model requests to http://localhost:8081/v1")
  }
  return url
}

// Use direct HTTP so HTTP_PROXY/HTTPS_PROXY and custom SDK fetch functions cannot
// reroute model traffic. Redirects are rejected rather than followed.
export async function fetchLocal(input: string | URL | Request, init?: RequestInit): Promise<Response> {
  const message = new Request(input, init)
  const url = assertURL(message.url)
  const body = message.body ? Buffer.from(await message.arrayBuffer()) : undefined
  return new Promise((resolve, reject) => {
    const headers = Object.fromEntries(message.headers.entries())
    headers["accept-encoding"] = "identity"
    const client = request(url, { method: message.method, headers, signal: message.signal }, (response) => {
      const status = response.statusCode ?? 500
      if (status >= 300 && status < 400) {
        response.resume()
        reject(new Error("Local model proxy redirects are disabled"))
        return
      }
      const headers = new Headers()
      for (let i = 0; i < response.rawHeaders.length; i += 2) {
        headers.append(response.rawHeaders[i], response.rawHeaders[i + 1])
      }
      resolve(new Response(
        message.method === "HEAD" || status === 204 || status === 304
          ? null
          : Readable.toWeb(response) as ReadableStream<Uint8Array>,
        { status, headers },
      ))
    })
    client.on("error", reject)
    client.end(body)
  })
}

export function modelIDs(input: unknown) {
  if (!input || typeof input !== "object" || !("data" in input) || !Array.isArray(input.data)) {
    throw new Error("Local proxy /v1/models must return an OpenAI-compatible data array")
  }
  return [...new Set(input.data.flatMap((model: unknown) => {
    if (!model || typeof model !== "object" || !("id" in model) || typeof model.id !== "string") return []
    if (!model.id.trim() || /[\u0000-\u001f\u007f]/.test(model.id)) return []
    return [model.id]
  }))].sort()
}

export async function discover(apiKey?: string) {
  const response = await fetchLocal(baseURL + "/models", {
    headers: apiKey ? { authorization: "Bearer " + apiKey } : {},
    signal: AbortSignal.timeout(3000),
  })
  if (!response.ok) throw new Error("Local proxy model discovery failed: HTTP " + response.status)
  return modelIDs(await response.json())
}

export function catalog(ids: string[]): ModelsDev.Provider {
  return {
    id,
    name: "localhost:8081",
    env: [],
    api: baseURL,
    npm: "@ai-sdk/openai-compatible",
    models: Object.fromEntries(ids.map((id) => [id, {
      id,
      name: id,
      release_date: "",
      attachment: false,
      reasoning: false,
      temperature: true,
      tool_call: true,
      modalities: { input: ["text"], output: ["text"] },
      limit: { context: 32768, output: 4096 },
    }])),
  }
}

export * as LocalProxy from "./local-proxy"
