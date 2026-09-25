param([string]$OutputDirectory = "portable-dist")
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$output = [IO.Path]::GetFullPath((Join-Path $repo $OutputDirectory))
# Do not accidentally include previous portable data or stale build files.
if (Test-Path -LiteralPath $output) { throw "Output directory already exists: $output" }
New-Item -ItemType Directory -Path $output | Out-Null
$desktopSource = Join-Path $repo "packages/desktop/dist/win-unpacked"
if (-not (Test-Path (Join-Path $desktopSource "OpenCode.exe"))) { throw "Build the portable desktop first" }
if (Test-Path (Join-Path $desktopSource "data")) { throw "Refusing to package a used desktop profile" }
$desktop = Join-Path $output "desktop"
$tui = Join-Path $output "tui"
Copy-Item -LiteralPath $desktopSource -Destination $desktop -Recurse
New-Item -ItemType Directory -Path "$tui/app" -Force | Out-Null
$download = Join-Path $output "upstream-tui.zip"
Invoke-WebRequest -Uri "https://github.com/anomalyco/opencode/releases/download/v1.18.32/opencode-windows-x64.zip" -OutFile $download
$expected = "1483c72d5adced825590a0ecf8cc18b3e87e535960a125dbf539d33bce135d0f"
if ((Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw "Upstream TUI checksum mismatch" }
Expand-Archive -LiteralPath $download -DestinationPath "$tui/app"
Copy-Item "$PSScriptRoot/Start-TUI.cmd" "$tui/Start-TUI.cmd"
foreach ($dir in @($desktop, $tui)) {
  Copy-Item "$PSScriptRoot/README.md" "$dir/README.md"
  Copy-Item "$repo/LICENSE" "$dir/LICENSE"
  @{
    version = "1.18.32"
    upstreamCommit = "545f51d26cc39a907d2867492d498d9607ea5fa4"
    sourceCommit = (& git -C $repo rev-parse HEAD)
    tuiUpstreamSha256 = $expected
    desktop = "Built from pinned source with portable data-path support; unsigned custom build"
  } | ConvertTo-Json | Set-Content -LiteralPath "$dir/BUILD.json" -Encoding utf8
  $name = Split-Path -Leaf $dir
  $zip = Join-Path $output "opencode-$name-portable.zip"
  Compress-Archive -LiteralPath $dir -DestinationPath $zip -CompressionLevel Optimal
  # Validate actual archive entries against a 100-character destination prefix.
  # Keep the full path below 240 characters for legacy Windows extractors.
  $archive = [IO.Compression.ZipFile]::OpenRead($zip)
  try {
    $longest = $archive.Entries | Sort-Object { $_.FullName.Length } -Descending | Select-Object -First 1
    if (-not $longest) { throw "Empty portable archive: $zip" }
    $length = $longest.FullName.Length
    Write-Host "$name longest ZIP entry ($length characters): $($longest.FullName)"
    if (100 + $length -ge 240) {
      throw "Portable ZIP exceeds the Windows extraction path budget: $($longest.FullName)"
    }
  } finally {
    $archive.Dispose()
  }
}
Get-ChildItem -LiteralPath $output -Filter "*-portable.zip" | ForEach-Object {
  "$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant())  $($_.Name)"
} | Set-Content -LiteralPath "$output/SHA256SUMS" -Encoding ascii
