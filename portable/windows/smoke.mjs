import assert from "node:assert/strict"
import { spawn, spawnSync } from "node:child_process"
import { once } from "node:events"
import { createServer } from "node:net"
import { mkdirSync, readFileSync, writeFileSync, readdirSync, renameSync, existsSync, cpSync } from "node:fs"
import { resolve, join, relative, isAbsolute } from "node:path"
import { setTimeout as delay } from "node:timers/promises"
import { chromium } from "playwright"

const output = resolve("portable-dist")
const root = join(output, "smoke workspace")
mkdirSync(root)
const logs = join(output, "smoke-logs")
mkdirSync(logs)
const results = []
let active
let proxy
const proxyLog = join(logs, "proxy-calls.json")
const hostile = {
  model: "openai/cloud-test",
  small_model: "openai/cloud-test",
  enabled_providers: ["openai"],
  disabled_providers: ["local-proxy"],
  provider: {
    openai: { options: { baseURL: "http://localhost:8082/v1", apiKey: "synthetic" }, models: { "cloud-test": {} } },
    "local-proxy": { options: { baseURL: "http://localhost:8082/v1" }, models: { "injected-model": {} } },
  },
}
async function tuiCommand(dir, args) {
  const child = spawn("cmd.exe", ["/d", "/s", "/c", '""' + join(dir, "Start-TUI.cmd") + '" ' + args + '"'], {
    windowsVerbatimArguments: true, windowsHide: true, cwd: dir,
    env: { ...process.env, OPENAI_API_KEY: "synthetic", OPENCODE_LOCAL_PROXY_ONLY: "0" },
    signal: AbortSignal.timeout(60000),
  })
  let stdout = ""
  let stderr = ""
  child.stdout.on("data", (chunk) => stdout += chunk)
  child.stderr.on("data", (chunk) => stderr += chunk)
  const [code] = await once(child, "exit")
  return { code, stdout: stdout.trim(), stderr }
}

function check(name, details = {}) {
  results.push({ name, status: "passed", ...details })
}
async function move(from, to) {
  for (const path of [from, to]) {
    const rel = relative(root, resolve(path))
    assert(!rel.startsWith("..") && !isAbsolute(rel), "Test move must stay within smoke workspace")
  }
  // Windows scanners and exiting child processes can briefly retain file handles.
  const deadline = Date.now() + 30000
  while (true) {
    try {
      renameSync(from, to)
      return
    } catch (error) {
      if (!["EPERM", "EBUSY", "EACCES"].includes(error.code) || Date.now() >= deadline) throw error
      await delay(500)
    }
  }
}
function unpack(name, folder) {
  const archive = join(output, name + ".zip")
  const result = spawnSync("pwsh", ["-NoProfile", "-Command",
    "Expand-Archive -LiteralPath $env:PORTABLE_TEST_ZIP -DestinationPath $env:PORTABLE_TEST_DEST"], {
    env: { ...process.env, PORTABLE_TEST_ZIP: archive, PORTABLE_TEST_DEST: root },
    encoding: "utf8", windowsHide: true, timeout: 120000,
  })
  assert.equal(result.status, 0, result.stderr)
  return join(root, folder)
}
function tui(dir, args) {
  const command = '""' + join(dir, "Start-TUI.cmd") + '" ' + args + '"'
  const result = spawnSync("cmd.exe", ["/d", "/s", "/c", command], {
    windowsVerbatimArguments: true, windowsHide: true, encoding: "utf8", timeout: 60000,
    cwd: dir,
    env: { ...process.env, OPENCODE_DB: ":memory:", XDG_DATA_HOME: join(root, "wrong-profile") },
  })
  assert.equal(result.status, 0, result.stderr || result.error?.message)
  return result.stdout.trim()
}
async function start(dir, attempt) {
  const reservation = createServer()
  await new Promise((r) => reservation.listen(0, "127.0.0.1", r))
  const port = reservation.address().port
  await new Promise((r) => reservation.close(r))
  const child = spawn(join(dir, "OpenCode.exe"), [
    "--remote-debugging-port=" + port, "--remote-debugging-address=127.0.0.1",
  ], {
    cwd: dir, windowsHide: true,
    env: {
      ...process.env, OPENCODE_DB: join(root, "installed-sentinel.db"),
      XDG_DATA_HOME: join(root, "wrong-profile"),
      OPENCODE_TEST_ONBOARDING: "1", OPENCODE_SIDECAR_V2: "1",
      OPENAI_API_KEY: "synthetic", OPENCODE_LOCAL_PROXY_ONLY: "0",
    },
    stdio: ["ignore", "pipe", "pipe"],
  })
  active = child
  const lines = []
  child.stdout.on("data", (chunk) => lines.push(chunk.toString()))
  child.stderr.on("data", (chunk) => lines.push(chunk.toString()))
  child.on("exit", () => writeFileSync(join(logs, attempt + ".log"), lines.join("")))
  const endpoint = "http://127.0.0.1:" + port
  const deadline = Date.now() + 90000
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw Error("Desktop exited: " + child.exitCode)
    if (await fetch(endpoint + "/json/version").then(r => r.ok).catch(() => false)) break
    await delay(300)
  }
  const browser = await chromium.connectOverCDP(endpoint, { timeout: 10000 })
  let page
  while (Date.now() < deadline) {
    page = browser.contexts().flatMap(c => c.pages()).find(p => p.url().startsWith("oc://renderer"))
    if (page) break
    await delay(300)
  }
  assert(page, "Packaged renderer did not appear")
  await page.waitForFunction(() => Boolean(window.api?.awaitInitialization), { timeout: 60000 })
  const server = await page.evaluate(() => window.api.awaitInitialization())
  const request = async (path, options = {}) => {
    const response = await fetch(server.url + path, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: "Basic " + Buffer.from(server.username + ":" + server.password).toString("base64"),
      },
      signal: AbortSignal.timeout(15000),
    })
    assert(response.ok, path + ": HTTP " + response.status)
    return response.json()
  }
  await request("/global/health")
  await page.locator("body").waitFor({ state: "visible" })
  assert((await page.locator("body").innerText()).trim().length > 10, "Renderer body is empty")
  await page.screenshot({ path: join(output, "desktop.png") })
  return {
    page, request,
    async close() {
      const exited = once(child, "exit")
      await page.close()
      const code = await Promise.race([exited, delay(20000).then(() => { throw Error("Desktop did not close cleanly") })])
      assert.equal(code[0], 0)
      await browser.close()
      active = undefined
    },
  }
}

try {
  let cli = unpack("opencode-tui-portable", "tui")
  assert.equal(tui(cli, "--version"), "1.18.32")
  check("TUI version")
  assert.equal(tui(cli, "db path"), join(cli, "data", "share", "opencode", "opencode.db"))
  tui(cli, 'db "CREATE TABLE portable_probe (value TEXT)"')
  tui(cli, 'db "INSERT INTO portable_probe VALUES (42)"')
  assert.match(tui(cli, 'db "SELECT value FROM portable_probe"'), /42/)
  check("TUI database survives restart")
  const movedCli = join(root, "TUI moved")
  await move(cli, movedCli)
  cli = movedCli
  assert.match(tui(cli, 'db "SELECT value FROM portable_probe"'), /42/)
  assert.equal(tui(cli, "db path"), join(cli, "data", "share", "opencode", "opencode.db"))
  check("TUI database persistence and relocation")
  writeFileSync(join(cli, "opencode.json"), JSON.stringify(hostile))
  const offline = await tuiCommand(cli, "models")
  assert.equal(offline.code, 0, offline.stderr)
  assert.equal(offline.stdout, "", "Offline proxy must not expose cloud models")
  check("TUI has no cloud fallback when proxy is offline")
  proxy = spawn(process.execPath, ["portable/windows/proxy-fixture.mjs"], {
    env: { ...process.env, PORTABLE_PROXY_LOG: proxyLog },
    stdio: ["ignore", "pipe", "pipe", "ipc"], windowsHide: true,
  })
  proxy.stderr.on("data", (chunk) => process.stderr.write(chunk))
  await Promise.race([once(proxy, "message"), once(proxy, "exit").then(() => { throw Error("Proxy fixture exited") }), delay(10000).then(() => { throw Error("Proxy fixture startup timed out") })])
  const models = await tuiCommand(cli, "models")
  assert.equal(models.code, 0, models.stderr)
  assert.deepEqual(models.stdout.split(/\r?\n/).sort(), ["local-proxy/proxy-small", "local-proxy/proxy-test"])
  check("TUI only lists proxy models despite cloud keys and hostile configuration")
  const attach = await tuiCommand(cli, "attach http://localhost:8082")
  assert.notEqual(attach.code, 0)
  assert.match(attach.stderr, /disabled/)
  check("TUI cannot attach to an unrestricted backend")
  writeFileSync(join(root, "installed-sentinel.db"), "do not touch")
  let desktop = unpack("opencode-desktop-portable", "desktop")
  const project = join(root, "project")
  mkdirSync(project)
  writeFileSync(join(project, "opencode.json"), JSON.stringify(hostile))
  const directory = "?directory=" + encodeURIComponent(project)
  const first = await start(desktop, "first")
  await first.page.keyboard.press("Control+,")
  const settingsDialog = first.page.getByRole("dialog")
  await settingsDialog.waitFor({ state: "visible", timeout: 15000 })
  assert.equal(await settingsDialog.getByRole("tab", { name: "Providers", exact: true }).count(), 0)
  assert.equal(await settingsDialog.getByRole("tab", { name: "Servers", exact: true }).count(), 0)
  await first.page.keyboard.press("Escape")
  await settingsDialog.waitFor({ state: "hidden", timeout: 15000 })
  check("Desktop hides provider and remote server configuration")
  await first.page.evaluate(() => window.api.storeSet("portable.smoke", "marker", "preserved"))
  const session = await first.request("/session" + directory, { method: "POST", body: JSON.stringify({ title: "Portable smoke" }) })
  assert(session.id)
  const providers = await first.request("/provider" + directory)
  assert.deepEqual(providers.all.map((p) => p.id), ["local-proxy"])
  assert.deepEqual(Object.keys(providers.all[0].models).sort(), ["proxy-small", "proxy-test"])
  assert.deepEqual(await first.request("/provider/auth" + directory), {})
  const config = await first.request("/config" + directory)
  assert.deepEqual(config.enabled_providers, ["local-proxy"])
  check("Desktop exposes only the local proxy and no cloud OAuth")
  const reply = await first.request("/session/" + session.id + "/message" + directory, {
    method: "POST",
    body: JSON.stringify({ model: { providerID: "local-proxy", modelID: "proxy-test" }, parts: [{ type: "text", text: "Synthetic routing check" }] }),
  })
  assert(reply.parts.some((p) => p.type === "text" && p.text.includes("LOCAL_PROXY_SMOKE_OK")), JSON.stringify(reply))
  const calls = JSON.parse(readFileSync(proxyLog, "utf8"))
  assert(calls.some((call) => call.path === "/v1/chat/completions" && call.model === "proxy-test"))
  check("Desktop routes a synthetic response through localhost:8081")
  const rejected = await tuiCommand(cli, 'run -m openai/cloud-test "Synthetic blocked-provider check"')
  assert.match(rejected.stderr + rejected.stdout, /Model not found|ProviderModelNotFoundError|not found/i)
  check("Cloud model execution is rejected")
  const injected = await tuiCommand(cli, 'run -m local-proxy/injected-model "Synthetic unlisted-model check"')
  assert.match(injected.stderr + injected.stdout, /Model not found|ProviderModelNotFoundError|not found/i)
  check("Unlisted proxy model execution is rejected")
  await first.page.evaluate(() => window.api.setDefaultServerUrl("http://localhost:8082"))
  assert.equal(await first.page.evaluate(() => window.api.getDefaultServerUrl()), null)
  check("Desktop ignores unrestricted default backend settings")
  await first.close()
  check("Desktop renderer and authenticated backend")
  assert(existsSync(join(desktop, "data", "share", "opencode", "opencode.db")))
  const second = await start(desktop, "restart")
  assert.equal(await second.page.evaluate(() => window.api.storeGet("portable.smoke", "marker")), "preserved")
  assert.equal((await second.request("/session/" + session.id + directory)).id, session.id)
  await second.close()
  check("Desktop settings and session survive restart")
  const movedDesktop = join(root, "Desktop moved")
  await move(desktop, movedDesktop)
  desktop = movedDesktop
  const third = await start(desktop, "relocated")
  assert.equal(await third.page.evaluate(() => window.api.storeGet("portable.smoke", "marker")), "preserved")
  assert.equal((await third.request("/session/" + session.id + directory)).id, session.id)
  await third.close()
  check("Desktop settings and session survive relocation")
  assert.equal(readFileSync(join(root, "installed-sentinel.db"), "utf8"), "do not touch")
  assert(!existsSync(join(root, "wrong-profile")))
  check("Inherited installed-profile paths ignored")
  const logRoot = join(desktop, "data", "desktop", "logs")
  const mainLogs = readdirSync(logRoot).map(d => join(logRoot, d, "main.log")).filter(existsSync).map(p => readFileSync(p, "utf8")).join("\n")
  assert(!mainLogs.includes("Checking for update"))
  assert(mainLogs.includes("1.18.32"))
  check("Pinned desktop version and no installer update check")
  const proxyExited = once(proxy, "exit")
  proxy.kill()
  await proxyExited
  proxy = undefined
  const offlineDesktop = await start(desktop, "offline")
  const offlineProviders = await offlineDesktop.request("/provider" + directory)
  assert.deepEqual(offlineProviders.all.map((p) => p.id), ["local-proxy"])
  assert.deepEqual(offlineProviders.all[0].models, {})
  assert.deepEqual(offlineProviders.default, {})
  await offlineDesktop.close()
  check("Desktop starts offline with no cloud fallback")
} catch (error) {
  results.push({ name: "failure", status: "failed", message: error.stack })
  process.exitCode = 1
} finally {
  if (active && active.exitCode === null) active.kill()
  if (proxy && proxy.exitCode === null) proxy.kill()
  // Only synthetic test data is copied into diagnostic artifacts.
  for (const dir of readdirSync(root)) {
    const source = join(root, dir, "data", "desktop", "logs")
    if (existsSync(source)) cpSync(source, join(logs, dir), { recursive: true })
  }
  writeFileSync(join(output, "smoke-report.json"), JSON.stringify({ results }, null, 2))
  console.log(JSON.stringify({ results }, null, 2))
}
