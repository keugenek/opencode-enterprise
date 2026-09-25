// Replaced by the restricted TUI build; runtime environment variables cannot change it.
declare const OPENCODE_LOCAL_PROXY_ONLY: boolean | undefined
export const localProxyOnly = typeof OPENCODE_LOCAL_PROXY_ONLY !== "undefined" && OPENCODE_LOCAL_PROXY_ONLY
