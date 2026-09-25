// Use the package entrypoint explicitly: Bun 1.3.14 substitutes a fetch-backed
// compatibility shim for bare "undici" imports and ignores its dispatcher.
import { Agent, request, type Dispatcher } from "undici/index.js"
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

// An explicit Undici dispatcher bypasses environment proxy settings under both
// Node and Bun (Bun's node:http wrapper uses its environment-aware fetch).
const direct = new Agent()

export async function fetchLocal(input: string | URL | Request, init?: RequestInit): Promise<Response> {
  const message = new Request(input, init)
  const url = assertURL(message.url)
  const body = message.body ? Buffer.from(await message.arrayBuffer()) : undefined
  const headers = Object.fromEntries(message.headers.entries())
  headers["accept-encoding"] = "identity"
  const response = await request(url, {
    dispatcher: direct,
    method: message.method as Dispatcher.HttpMethod,
    headers,
    body,
    signal: message.signal,
    maxRedirections: 0,
  })
  const status = response.statusCode
  if (status >= 300 && status < 400) {
    // Destroying an unread Undici body emits an expected asynchronous AbortError.
    response.body.on("error", () => {})
    response.body.destroy()
    throw new Error("Local model proxy redirects are disabled")
  }
  const responseHeaders = new Headers()
  for (const [name, value] of Object.entries(response.headers)) {
    if (Array.isArray(value)) value.forEach((item) => responseHeaders.append(name, item))
    else if (value !== undefined) responseHeaders.set(name, value)
  }
  return new Response(
    message.method === "HEAD" || status === 204
      ? null
      : // Node and Bun declare different types for the same Web Stream contract.
        Readable.toWeb(response.body) as unknown as ReadableStream<Uint8Array>,
    { status, headers: responseHeaders },
  )
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
