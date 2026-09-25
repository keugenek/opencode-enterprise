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

function check(name, details = {}) {
  results.push({ name, status: "passed", ...details })
}
function move(from, to) {
  for (const path of [from, to]) {
    const rel = relative(root, resolve(path))
    assert(!rel.startsWith("..") && !isAbsolute(rel), "Test move must stay within smoke workspace")
  }
  renameSync(from, to)
}
function unpack(name) {
  const archive = join(output, name + ".zip")
  const result = spawnSync("pwsh", ["-NoProfile", "-Command",
    "Expand-Archive -LiteralPath $env:PORTABLE_TEST_ZIP -DestinationPath $env:PORTABLE_TEST_DEST"], {
    env: { ...process.env, PORTABLE_TEST_ZIP: archive, PORTABLE_TEST_DEST: root },
    encoding: "utf8", windowsHide: true, timeout: 120000,
  })
  assert.equal(result.status, 0, result.stderr)
  return join(root, name)
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
  let cli = unpack("opencode-tui-1.18.32-windows-x64-portable")
  assert.equal(tui(cli, "--version"), "1.18.32")
  check("TUI version")
  assert.equal(tui(cli, "db path"), join(cli, "data", "share", "opencode", "opencode.db"))
  tui(cli, 'db "CREATE TABLE portable_probe (value TEXT)"')
  tui(cli, 'db "INSERT INTO portable_probe VALUES (42)"')
  assert.match(tui(cli, 'db "SELECT value FROM portable_probe"'), /42/)
  const movedCli = join(root, "TUI moved")
  move(cli, movedCli)
  cli = movedCli
  assert.match(tui(cli, 'db "SELECT value FROM portable_probe"'), /42/)
  assert.equal(tui(cli, "db path"), join(cli, "data", "share", "opencode", "opencode.db"))
  check("TUI database persistence and relocation")
  writeFileSync(join(root, "installed-sentinel.db"), "do not touch")
  let desktop = unpack("opencode-desktop-1.18.32-windows-x64-portable")
  const project = join(root, "project")
  mkdirSync(project)
  const directory = "?directory=" + encodeURIComponent(project)
  const first = await start(desktop, "first")
  await first.page.evaluate(() => window.api.storeSet("portable.smoke", "marker", "preserved"))
  const session = await first.request("/session" + directory, { method: "POST", body: JSON.stringify({ title: "Portable smoke" }) })
  assert(session.id)
  await first.close()
  check("Desktop renderer and authenticated backend")
  assert(existsSync(join(desktop, "data", "share", "opencode", "opencode.db")))
  const second = await start(desktop, "restart")
  assert.equal(await second.page.evaluate(() => window.api.storeGet("portable.smoke", "marker")), "preserved")
  assert.equal((await second.request("/session/" + session.id + directory)).id, session.id)
  await second.close()
  check("Desktop settings and session survive restart")
  const movedDesktop = join(root, "Desktop moved")
  move(desktop, movedDesktop)
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
} catch (error) {
  results.push({ name: "failure", status: "failed", message: error.stack })
  process.exitCode = 1
} finally {
  if (active && active.exitCode === null) active.kill()
  // Only synthetic test data is copied into diagnostic artifacts.
  for (const dir of readdirSync(root)) {
    const source = join(root, dir, "data", "desktop", "logs")
    if (existsSync(source)) cpSync(source, join(logs, dir), { recursive: true })
  }
  writeFileSync(join(output, "smoke-report.json"), JSON.stringify({ results }, null, 2))
  console.log(JSON.stringify({ results }, null, 2))
}
