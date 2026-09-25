import { afterAll, beforeAll, expect, test } from "bun:test"
import { createServer } from "node:http"
import { LocalProxy } from "../src/local-proxy"

let requests = 0
let authorization: string | undefined
let redirected = 0
const sink = createServer((_req, res) => { redirected++; res.end("unexpected") })
const server = createServer((req, res) => {
  requests++
  authorization = req.headers.authorization
  if (req.url === "/v1/redirect") {
    const address = sink.address()
    if (!address || typeof address === "string") throw Error("sink unavailable")
    res.writeHead(302, { location: "http://127.0.0.1:" + address.port + "/escape" })
    res.end()
    return
  }
  if (req.url === "/v1/models") {
    res.setHeader("content-type", "application/json")
    res.end(JSON.stringify({ data: [{ id: "proxy-test" }, { id: "proxy-test" }] }))
    return
  }
  req.pipe(res)
})
beforeAll(async () => {
  await new Promise<void>((resolve) => sink.listen(0, "127.0.0.1", resolve))
  await new Promise<void>((resolve) => server.listen(8081, resolve))
})
afterAll(async () => {
  server.closeAllConnections()
  sink.closeAllConnections()
  await Promise.all([new Promise<void>((resolve) => server.close(() => resolve())), new Promise<void>((resolve) => sink.close(() => resolve()))])
})
test("discovers only the local proxy model IDs", async () => {
  expect(await LocalProxy.discover()).toEqual(["proxy-test"])
  expect(LocalProxy.catalog(["proxy-test"]).api).toBe("http://localhost:8081/v1")
})
test("rejects alternate origins, ports, credentials and paths before connecting", async () => {
  const before = requests
  for (const url of [
    "https://api.openai.com/v1/chat/completions",
    "http://localhost:8082/v1/chat/completions",
    "http://localhost.example.com:8081/v1/models",
    "http://user:pass@localhost:8081/v1/models",
    "http://localhost:8081/other",
  ]) {
    await expect(LocalProxy.fetchLocal(url)).rejects.toThrow()
  }
  expect(requests).toBe(before)
})
test("rejects redirects without contacting their target", async () => {
  await expect(LocalProxy.fetchLocal(LocalProxy.baseURL + "/redirect")).rejects.toThrow("redirects")
  expect(redirected).toBe(0)
})
test("forwards body and authentication directly, regardless of proxy environment", async () => {
  const original = process.env.HTTP_PROXY
  process.env.HTTP_PROXY = "http://127.0.0.1:1"
  try {
    const response = await LocalProxy.fetchLocal(LocalProxy.baseURL + "/chat/completions", {
      method: "POST", headers: { "content-type": "application/json", authorization: "Bearer local-test" }, body: JSON.stringify({ model: "proxy-test" }),
    })
    expect(await response.json()).toEqual({ model: "proxy-test" })
    expect(authorization).toBe("Bearer local-test")
  } finally {
    if (original === undefined) delete process.env.HTTP_PROXY
    else process.env.HTTP_PROXY = original
  }
})
test("rejects malformed discovery without inventing a cloud fallback", () => {
  expect(() => LocalProxy.modelIDs({ models: ["gpt-4"] })).toThrow()
  expect(LocalProxy.modelIDs({ data: [{ id: "" }, { nope: true }, { id: "valid" }] })).toEqual(["valid"])
})
