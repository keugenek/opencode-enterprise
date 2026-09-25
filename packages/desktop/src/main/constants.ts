import { app } from "electron"

type Channel = "dev" | "beta" | "prod"
const raw = import.meta.env.OPENCODE_CHANNEL
export const CHANNEL: Channel = raw === "dev" || raw === "beta" || raw === "prod" ? raw : "dev"

export const PORTABLE =
  app.isPackaged && process.platform === "win32" && import.meta.env.OPENCODE_PORTABLE === "1"
export const UPDATER_ENABLED = app.isPackaged && CHANNEL !== "dev" && !PORTABLE
