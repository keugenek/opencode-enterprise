#!/usr/bin/env node
// Run the packaged Electron application, its bundled renderer and real V1
// utility-process sidecar. Only the native directory picker is stubbed, following
// https://playwright.dev/docs/api/class-electron#mocking-native-dialogs .
import assert from "node:assert/strict"
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises"
import { createRequire } from "node:module"
import os from "node:os"
import path from "node:path"

const [executable, source, output] = process.argv.slice(2)
assert(executable && source && output, "Usage: node smoke-desktop.mjs <packaged.exe> <patched-source> <screenshot.png>")
assert.equal(process.platform, "win32", "This acceptance smoke targets the native Windows package")
const { _electron, expect } = createRequire(path.join(path.resolve(source), "packages/app/package.json"))(
  "@playwright/test",
)
const policy = JSON.parse(await readFile("C:\\Program Files\\OpenCode Enterprise\\enterprise.json", "utf8"))
const screenshot = path.resolve(output)
const scratch = await mkdtemp(path.join(os.tmpdir(), "opencode-desktop-smoke-"))
const workspace = path.join(scratch, "project")
const appdata = path.join(scratch, "appdata")
const netlog = path.join(scratch, "network.json")
await Promise.all([mkdir(workspace), mkdir(appdata), mkdir(path.dirname(screenshot), { recursive: true })])
await writeFile(
  path.join(workspace, "README.md"),
  "# Enterprise desktop smoke\nLocal UI and policy checks; no inference evaluation.\n",
)

const checks = []
const requests = new Set()
const failures = []
const secrets = new Set()
const diagnostics = { consoleErrors: [], requestFailures: [], httpErrors: [], rendererErrors: failures }
const running = { app: undefined, page: undefined }
const report = {
  kind: "native-windows-desktop-smoke",
  checks,
  inference: "not-run",
  result: "failed",
  passed: false,
  diagnostics,
}

function safeURL(raw) {
  if (!URL.canParse(raw)) return "[invalid URL]"
  const url = new URL(raw)
  if (!["http:", "https:", "ws:", "wss:", "oc:"].includes(url.protocol)) return url.protocol
  return `${url.protocol}//${url.host}${url.pathname}`
}

function safeText(raw) {
  let text = String(raw)
  for (const secret of secrets) text = text.replaceAll(secret, "[redacted]")
  return text
    .replace(/\b(?:Basic|Bearer)\s+[A-Za-z0-9._~+/=-]+/gi, "[redacted authorization]")
    .replace(/(?:https?|wss?|oc):\/\/[^\s<>"']+/gi, safeURL)
    .slice(0, 4000)
}

const observedPages = new WeakSet()
function observePage(page) {
  if (observedPages.has(page)) return
  observedPages.add(page)
  page.on("websocket", (socket) => requests.add(socket.url()))
  page.on("pageerror", (error) => failures.push(safeText(error.message)))
  page.on("console", (message) => {
    if (message.type() !== "error") return
    diagnostics.consoleErrors.push({ text: safeText(message.text()), url: safeURL(message.location().url) })
  })
}

function allowed(raw, origin) {
  const url = new URL(raw)
  if (["data:", "blob:", "about:"].includes(url.protocol)) return true
  if (url.protocol === "oc:" && url.hostname === "renderer") return true
  return (
    (url.protocol === "http:" && url.origin === origin) ||
    (url.protocol === "ws:" && url.origin === origin.replace(/^http:/, "ws:"))
  )
}

function eventURLs(value) {
  if (typeof value === "string") return /^(https?|wss?):\/\//i.test(value) ? [value] : []
  if (!value || typeof value !== "object") return []
  return Object.values(value).flatMap(eventURLs)
}

async function deadline(promise, label, ms = 45_000) {
  let timer
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(`${label} did not complete within ${ms} ms`)), ms)
      }),
    ])
  } finally {
    clearTimeout(timer)
  }
}

try {
  running.app = await _electron.launch({
    executablePath: path.resolve(executable),
    cwd: workspace,
    timeout: 60_000,
    chromiumSandbox: true,
    locale: "en-US",
    args: [`--log-net-log=${netlog}`, "--net-log-capture-mode=Default"],
    env: {
      ...process.env,
      APPDATA: appdata,
      LOCALAPPDATA: path.join(scratch, "localappdata"),
      XDG_DATA_HOME: path.join(scratch, "data"),
      XDG_STATE_HOME: path.join(scratch, "state"),
      XDG_CONFIG_HOME: path.join(scratch, "config"),
      XDG_CACHE_HOME: path.join(scratch, "cache"),
      // An enterprise package must ignore both unsupported launch overrides.
      ELECTRON_RENDERER_URL: "https://example.invalid",
      OPENCODE_SIDECAR_V2: "1",
    },
  })
  running.app.context().on("request", (request) => requests.add(request.url()))
  running.app.context().on("requestfailed", (request) => {
    diagnostics.requestFailures.push({
      url: safeURL(request.url()),
      error: safeText(request.failure()?.errorText ?? "unknown"),
    })
  })
  running.app.context().on("response", (response) => {
    if (response.status() < 400) return
    diagnostics.httpErrors.push({ url: safeURL(response.url()), status: response.status() })
  })
  running.app.context().on("page", observePage)
  running.page = await running.app.firstWindow({ timeout: 60_000 })
  const page = running.page
  observePage(page)
  page.setDefaultTimeout(30_000)
  await expect(page).toHaveURL(/^oc:\/\/renderer\//, { timeout: 60_000 })
  const native = await running.app.evaluate(({ app, BrowserWindow }) => {
    const windows = BrowserWindow.getAllWindows()
    return {
      packaged: app.isPackaged,
      count: windows.length,
      preferences: windows[0]?.webContents.getLastWebPreferences(),
    }
  })
  assert.equal(native.packaged, true, "Must test the actual packaged application")
  assert.equal(native.count, 1, "Unexpected additional native windows")
  assert.equal(native.preferences.contextIsolation, true)
  assert.equal(native.preferences.nodeIntegration, false)
  checks.push("packaged Electron window; bundled oc renderer; context isolation; no renderer Node integration")

  const connection = await deadline(
    page.evaluate(() => window.api.awaitInitialization()),
    "sidecar initialization",
  )
  const origin = new URL(connection.url)
  assert.equal(origin.protocol, "http:")
  assert.equal(origin.hostname, "127.0.0.1")
  assert(origin.port && origin.pathname === "/" && !origin.search && !origin.hash)
  assert.equal(connection.username, "opencode")
  assert.equal(typeof connection.password, "string")
  assert(connection.password.length >= 32, "Sidecar must supply a strong per-launch credential")
  const authorization = `Basic ${Buffer.from(`${connection.username}:${connection.password}`).toString("base64")}`
  secrets.add(connection.password)
  secrets.add(authorization)
  const api = (route, options = {}) => {
    const url = new URL(route, origin)
    url.searchParams.set("directory", workspace)
    return fetch(url, {
      ...options,
      headers: { Authorization: authorization, ...options.headers },
      signal: AbortSignal.timeout(20_000),
      redirect: "error",
    })
  }
  const health = await api("/global/health")
  assert.equal(health.status, 200)
  assert.equal((await health.json()).healthy, true)
  for (const route of ["/global/health", "/provider"]) {
    const response = await fetch(new URL(route, origin), { signal: AbortSignal.timeout(20_000), redirect: "error" })
    assert.equal(response.status, 401, `${route} must require authentication`)
    await response.arrayBuffer()
  }
  checks.push("live authenticated loopback V1 sidecar; unauthenticated health/provider rejected")

  const providers = await api("/provider")
  assert.equal(providers.status, 200)
  const initial = await providers.json()
  assert.deepEqual(
    initial.all.map((provider) => provider.id),
    ["enterprise"],
  )
  assert.deepEqual(initial.connected, ["enterprise"])
  assert.deepEqual(Object.keys(initial.all[0].models), [policy.model])
  checks.push("exactly one administrator-selected enterprise model")

  const untrusted = await api("/provider", { headers: { Origin: "https://untrusted.invalid" } })
  assert.equal(untrusted.status, 403, "Untrusted renderer origin must be rejected")
  await untrusted.arrayBuffer()
  for (const request of [
    {
      route: "/config",
      method: "PATCH",
      body: { model: "openai/gpt-4o", provider: { openai: { options: { apiKey: "smoke-invalid" } } } },
    },
    { route: "/auth/openai", method: "PUT", body: { type: "api", key: "smoke-invalid" } },
    {
      route: "/mcp",
      method: "POST",
      body: { name: "smoke", config: { type: "remote", url: "https://example.invalid/mcp" } },
    },
  ]) {
    const response = await api(request.route, {
      method: request.method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request.body),
    })
    assert.equal(response.status, 403, `${request.method} ${request.route} must be blocked`)
    await response.arrayBuffer()
  }
  const after = await api("/provider")
  assert.equal(after.status, 200)
  assert.deepEqual(await after.json(), initial, "Rejected mutations must not change model/provider policy")
  checks.push("foreign Origin, cloud configuration, provider credentials and MCP rejected")

  const created = await api("/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "Enterprise desktop policy smoke" }),
  })
  assert.equal(created.status, 200)
  const session = await created.json()
  assert.equal(typeof session.id, "string")
  const cloudPrompt = await api(`/session/${encodeURIComponent(session.id)}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: { providerID: "openai", modelID: "gpt-4o" },
      parts: [{ type: "text", text: "This request must be rejected before model invocation." }],
    }),
  })
  assert.equal(cloudPrompt.status, 403, "Cloud model override must be rejected before inference")
  await cloudPrompt.arrayBuffer()
  checks.push("real session rejects a cloud-model prompt before inference")

  assert.equal(await page.evaluate(() => window.api.getDefaultServerUrl()), null)
  await page.evaluate(async () => {
    try {
      await window.api.setDefaultServerUrl("https://example.invalid")
    } catch {
      // Implementations may reject the setter or ignore the unsupported value.
    }
  })
  assert.equal(
    await page.evaluate(() => window.api.getDefaultServerUrl()),
    null,
    "Native IPC must not select a remote server",
  )
  assert.equal((await page.evaluate(() => window.api.updater.check())).status, "disabled")
  checks.push("native IPC cannot select a remote server; updater disabled")

  // Probe the renderer transport separately from Node's API client. Do not add
  // Authorization or bypass CORS: the production main-process hook supplies it.
  diagnostics.rendererHealth = await deadline(
    page.evaluate(async (endpoint) => {
      const context = {
        locationOrigin: location.origin,
        documentURL: `${location.protocol}//${location.host}${location.pathname}`,
      }
      try {
        const response = await fetch(endpoint, { signal: AbortSignal.timeout(15_000), redirect: "error" })
        await response.arrayBuffer()
        return { ...context, status: response.status, responseType: response.type }
      } catch (error) {
        return { ...context, error: error instanceof Error ? error.message : String(error) }
      }
    }, new URL("/global/health", origin).href),
    "renderer health diagnostic",
    20_000,
  )

  // Exercise the real renderer project-opening flow without an interactive OS
  // dialog. No application APIs, server responses or model results are mocked.
  await running.app.evaluate(({ dialog }, directory) => {
    dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [directory] })
  }, workspace)
  const rail = page.locator('[data-component="sidebar-rail"]:visible')
  await expect(rail.getByRole("button", { name: "Open project", exact: true })).toBeEnabled({ timeout: 60_000 })
  await rail.getByRole("button", { name: "Open project", exact: true }).click()
  const composer = page.locator('[data-component="prompt-input"][contenteditable="true"]')
  await expect(composer).toBeEditable({ timeout: 60_000 })
  await expect(page.locator('[data-component="enterprise-model"]')).toHaveText(policy.model, { timeout: 30_000 })
  await composer.fill("Enterprise desktop is ready. This smoke test does not send a model request.")
  await rail.getByRole("button", { name: "Settings", exact: true }).click()
  const settings = page.getByRole("dialog")
  await expect(settings.getByRole("tab", { name: "General", exact: true })).toBeVisible()
  for (const name of ["Providers", "Models", "Servers"]) {
    await expect(settings.getByRole("tab", { name, exact: true })).toHaveCount(0)
  }
  for (const selector of [
    '[data-action="prompt-model"]',
    '[data-action="settings-auto-accept-permissions"]',
    '[data-action="settings-shell"]',
    '[data-component="getting-started"]',
  ])
    await expect(page.locator(`${selector}:visible`)).toHaveCount(0)
  await page.keyboard.press("Escape")
  await expect(settings).toHaveCount(0)
  await expect(composer).toBeEditable()
  await page.screenshot({ path: screenshot, fullPage: true })
  checks.push(
    "standard project/composer UI editable; fixed model visible; provider, shell-configuration and auto-accept settings absent",
  )

  // Flush Chromium's startup capture before inspecting it. Renderer event
  // subscriptions alone miss requests made before Playwright attaches.
  await running.app.evaluate(async ({ netLog }) => {
    await netLog.stopLogging()
  })
  const network = JSON.parse(await readFile(netlog, "utf8"))
  assert(Array.isArray(network.events) && network.events.length > 0, "Missing Chromium startup network evidence")
  for (const event of network.events) for (const url of eventURLs(event.params)) requests.add(url)
  const external = [...requests].filter((url) => !allowed(url, origin.origin))
  assert.deepEqual(external, [], "Desktop attempted an external renderer/Chromium network request")
  assert.deepEqual(failures, [], "Renderer encountered an uncaught exception")
  checks.push("no external URLs in observed renderer requests or Chromium startup netlog")
  report.result = "passed"
  report.passed = true
  report.model = policy.model
  report.observedURLs = requests.size
  report.limitations = [
    "No live inference/private acceptance",
    "No OS-wide packet capture",
    "Missing-policy desktop startup not exercised; protected policy left untouched",
  ]
} catch (error) {
  report.error = safeText(error instanceof Error ? error.message : String(error))
  if (running.app) {
    await deadline(
      running.app.evaluate(async ({ netLog }) => {
        if (netLog.currentlyLogging) await netLog.stopLogging()
      }),
      "failure network capture",
      10_000,
    ).catch(() => {})
    await readFile(netlog, "utf8")
      .then((text) => {
        const network = JSON.parse(text)
        const sources = new Map()
        for (const event of network.events ?? []) {
          const urls = eventURLs(event.params)
          for (const url of urls) requests.add(url)
          if (urls.length) sources.set(event.source?.id, urls.map(safeURL))
        }
        diagnostics.networkErrors = (network.events ?? [])
          .filter((event) => typeof event.params?.net_error === "number" && event.params.net_error < 0)
          .map((event) => ({
            type: event.type,
            code: event.params.net_error,
            urls: sources.get(event.source?.id) ?? [],
          }))
      })
      .catch((error) => {
        diagnostics.networkCaptureError = safeText(error.message)
      })
  }
  if (running.page)
    await running.page
      .screenshot({ path: screenshot.replace(/\.png$/i, "-failure.png"), fullPage: true })
      .catch(() => {})
  throw error
} finally {
  diagnostics.observedURLs = [...new Set([...requests].map(safeURL))]
  if (running.app)
    await deadline(running.app.close(), "native application shutdown", 20_000).catch(() => running.app.process().kill())
  await writeFile(screenshot.replace(/\.png$/i, ".json"), `${JSON.stringify(report, null, 2)}\n`)
  await rm(scratch, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 }).catch(() => {})
  console.log(JSON.stringify(report))
}
