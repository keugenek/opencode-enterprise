import { afterEach, expect, test } from "bun:test"
import { mkdtempSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { initializePortable } from "./portable"

const environment = { ...process.env }
const roots: string[] = []
afterEach(() => {
  Object.keys(process.env).forEach((key) => {
    if (!(key in environment)) delete process.env[key]
  })
  Object.assign(process.env, environment)
  roots.forEach((root) => rmSync(root, { recursive: true, force: true }))
  roots.length = 0
})

test("keeps persistent data after restart and relocation, overriding installed paths", () => {
  const parent = mkdtempSync(join(tmpdir(), "opencode-portable-"))
  roots.push(parent)
  const root = join(parent, "original")
  process.env.OPENCODE_DB = ":memory:"
  process.env.XDG_DATA_HOME = join(parent, "installed")
  process.env.OPENCODE_TEST_ONBOARDING = "1"
  process.env.OPENCODE_SIDECAR_V2 = "1"
  const paths = initializePortable(root)
  writeFileSync(join(paths.userData, "marker"), "preserved")
  initializePortable(root)
  expect(readFileSync(join(paths.userData, "marker"), "utf8")).toBe("preserved")
  const moved = join(parent, "moved folder")
  renameSync(root, moved)
  const relocated = initializePortable(moved)
  expect(readFileSync(join(relocated.userData, "marker"), "utf8")).toBe("preserved")
  expect(process.env.OPENCODE_DB).toBe(join(moved, "share", "opencode", "opencode.db"))
  expect(process.env.XDG_DATA_HOME).toBe(join(moved, "share"))
  expect(process.env.OPENCODE_TEST_ONBOARDING).toBeUndefined()
  expect(process.env.OPENCODE_SIDECAR_V2).toBeUndefined()
})

test("fails without changing environment when the data root cannot be created", () => {
  const parent = mkdtempSync(join(tmpdir(), "opencode-portable-"))
  roots.push(parent)
  const blocked = join(parent, "file")
  writeFileSync(blocked, "not a directory")
  const original = process.env.OPENCODE_DB
  expect(() => initializePortable(blocked)).toThrow()
  expect(process.env.OPENCODE_DB).toBe(original)
})
