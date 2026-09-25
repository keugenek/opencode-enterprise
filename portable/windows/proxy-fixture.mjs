import { createServer } from "node:http"
import { writeFileSync } from "node:fs"

const calls = []
createServer(async (req, res) => {
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  const text = Buffer.concat(chunks).toString()
  const body = text ? JSON.parse(text) : {}
  calls.push({ path: req.url, model: body.model })
  writeFileSync(process.env.PORTABLE_PROXY_LOG, JSON.stringify(calls))
  if (req.url === "/v1/models") {
    res.setHeader("content-type", "application/json")
    res.end(JSON.stringify({ data: [{ id: "proxy-test" }, { id: "proxy-small" }] }))
    return
  }
  if (req.url !== "/v1/chat/completions") {
    res.writeHead(404)
    res.end()
    return
  }
  const message = { role: "assistant", content: "LOCAL_PROXY_SMOKE_OK" }
  if (!body.stream) {
    res.setHeader("content-type", "application/json")
    res.end(JSON.stringify({ id: "fixture", object: "chat.completion", created: 1, model: body.model, choices: [{ index: 0, message, finish_reason: "stop" }], usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 } }))
    return
  }
  res.setHeader("content-type", "text/event-stream")
  for (const choice of [{ index: 0, delta: message, finish_reason: null }, { index: 0, delta: {}, finish_reason: "stop" }]) {
    res.write("data: " + JSON.stringify({ id: "fixture", object: "chat.completion.chunk", created: 1, model: body.model, choices: [choice] }) + "\n\n")
  }
  res.end("data: [DONE]\n\n")
}).listen(8081, () => process.send("ready"))
