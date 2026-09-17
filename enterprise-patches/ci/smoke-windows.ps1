# Synthetic policy only, on a disposable administrator CI runner.
param([Parameter(Mandatory=$true)][string]$Binary,
      [Parameter(Mandatory=$true)][string]$Version)
$ErrorActionPreference = 'Stop'
$Binary = (Resolve-Path -LiteralPath $Binary).Path
$directory = 'C:\Program Files\OpenCode Enterprise'
$policy = "$directory\enterprise.json"
$original = [IO.File]::ReadAllBytes($policy)
$fileAcl = [IO.File]::GetAccessControl($policy)
$dirAcl = [IO.Directory]::GetAccessControl($directory)
$checks = 0
function Invoke-Check([string[]]$Arguments, [bool]$Allowed, [string]$Expected) {
  # Windows PowerShell represents native stderr as ErrorRecord; retain it without
  # letting ErrorActionPreference bypass the explicit exit-code assertion.
  $savedPreference = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  $output = (& $Binary @Arguments 2>&1 | Out-String).Trim()
  $code = $LASTEXITCODE
  $ErrorActionPreference = $savedPreference
  if (($code -eq 0) -ne $Allowed) { throw "Unexpected exit $code for $Arguments : $output" }
  if ($Expected -and $output -notmatch [regex]::Escape($Expected)) { throw "Missing expected response '$Expected': $output" }
  $script:checks++
}
try {
  Invoke-Check @('--version') $true $Version
  $env:OPENCODE_CONFIG_CONTENT = '{"model":"openai/forbidden","permission":"allow","provider":{"evil":{"npm":"untrusted"}}}'
  $env:OPENCODE_TEST_MANAGED_CONFIG_DIR = $env:RUNNER_TEMP
  $env:ProgramFiles = $env:RUNNER_TEMP
  $env:SystemRoot = $env:RUNNER_TEMP
  Invoke-Check @('models') $true 'enterprise/enterprise-coder'
  Remove-Item Env:OPENCODE_CONFIG_CONTENT, Env:OPENCODE_TEST_MANAGED_CONFIG_DIR
  $env:ProgramFiles = 'C:\Program Files'
  $env:SystemRoot = 'C:\Windows'
  foreach ($flag in @('--auto', '--yolo', '--dangerously-skip-permissions')) {
    Invoke-Check @($flag, '--version') $false 'Auto-approval is disabled'
  }
  # Actual NTFS rights, exercising the compiled reader rather than a mock.
  foreach ($rights in @('WriteData', 'AppendData', 'ChangePermissions', 'TakeOwnership', 'Delete')) {
    $acl = [IO.File]::GetAccessControl($policy)
    $rule = New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier('S-1-5-32-545')), $rights, 'Allow')
    [void]$acl.AddAccessRule($rule)
    [IO.File]::SetAccessControl($policy, $acl)
    Invoke-Check @('--version') $false 'Enterprise Windows policy rejected'
    [IO.File]::SetAccessControl($policy, $fileAcl)
  }
  $acl = [IO.Directory]::GetAccessControl($directory)
  $rule = New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier('S-1-5-32-545')), 'DeleteSubdirectoriesAndFiles', 'Allow')
  [void]$acl.AddAccessRule($rule)
  [IO.Directory]::SetAccessControl($directory, $acl)
  Invoke-Check @('--version') $false 'Enterprise Windows policy rejected'
  [IO.Directory]::SetAccessControl($directory, $dirAcl)
  $acl = [IO.File]::GetAccessControl($policy)
  $acl.SetOwner([Security.Principal.WindowsIdentity]::GetCurrent().User)
  [IO.File]::SetAccessControl($policy, $acl)
  Invoke-Check @('--version') $false 'Untrusted policy owner'
  [IO.File]::SetAccessControl($policy, $fileAcl)
  [IO.File]::WriteAllText($policy, '{invalid json')
  Invoke-Check @('--version') $false ''
  [IO.File]::WriteAllText($policy, ('x' * 16385))
  Invoke-Check @('--version') $false 'Policy exceeds 16 KiB'
  [IO.File]::WriteAllBytes($policy, $original)
  [IO.File]::Move($policy, "$policy.backup")
  try { Invoke-Check @('--version') $false 'Enterprise Windows policy rejected' }
  finally { [IO.File]::Move("$policy.backup", $policy) }
  # A junction to an otherwise protected directory must also be rejected.
  [IO.Directory]::Move($directory, "$directory.backup")
  try {
    New-Item -ItemType Junction -Path $directory -Target "$directory.backup" | Out-Null
    Invoke-Check @('--version') $false 'reparse point'
  } finally {
    if ([IO.Directory]::Exists($directory)) { [IO.Directory]::Delete($directory) }
    [IO.Directory]::Move("$directory.backup", $directory)
  }
  Invoke-Check @('--version') $true $Version
  Write-Output "Windows compiled-binary regression checks passed: $checks"
} finally {
  [IO.Directory]::SetAccessControl($directory, $dirAcl)
  [IO.File]::WriteAllBytes($policy, $original)
  [IO.File]::SetAccessControl($policy, $fileAcl)
}
