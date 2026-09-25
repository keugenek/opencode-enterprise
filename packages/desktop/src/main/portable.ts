import { mkdirSync, openSync, closeSync } from "node:fs"
import { join } from "node:path"

// Called before stores, Chromium sessions and the backend are initialized.
// Never fall back to the installed profile when the portable directory is unwritable.
export function initializePortable(root: string) {
  const paths = {
    userData: join(root, "desktop"),
    sessionData: join(root, "browser"),
    appData: join(root, "appdata"),
    temp: join(root, "tmp"),
    downloads: join(root, "downloads"),
    config: join(root, "config"),
    data: join(root, "share"),
    cache: join(root, "cache"),
    state: join(root, "state"),
  }
  Object.values(paths).forEach((path) => mkdirSync(path, { recursive: true }))
  mkdirSync(join(paths.data, "opencode"), { recursive: true })
  closeSync(openSync(join(root, ".portable"), "a"))
  Object.assign(process.env, {
    XDG_CONFIG_HOME: paths.config,
    XDG_DATA_HOME: paths.data,
    XDG_CACHE_HOME: paths.cache,
    XDG_STATE_HOME: paths.state,
    OPENCODE_DB: join(paths.data, "opencode", "opencode.db"),
    OPENCODE_DISABLE_AUTOUPDATE: "true",
    TEMP: paths.temp,
    TMP: paths.temp,
  })
  delete process.env.OPENCODE_TEST_ONBOARDING
  delete process.env.OPENCODE_SIDECAR_V2
  return paths
}
