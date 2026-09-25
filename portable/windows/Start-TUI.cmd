@echo off
setlocal DisableDelayedExpansion
set "XDG_CONFIG_HOME=%~dp0data\config"
set "XDG_DATA_HOME=%~dp0data\share"
set "XDG_CACHE_HOME=%~dp0data\cache"
set "XDG_STATE_HOME=%~dp0data\state"
set "OPENCODE_DB=%~dp0data\share\opencode\opencode.db"
set "OPENCODE_DISABLE_AUTOUPDATE=true"
set "OPENCODE_TEST_ONBOARDING="
set "OPENCODE_SIDECAR_V2="
set "TEMP=%~dp0data\tmp"
set "TMP=%TEMP%"
for %%D in ("%XDG_CONFIG_HOME%" "%XDG_DATA_HOME%\opencode" "%XDG_CACHE_HOME%" "%XDG_STATE_HOME%" "%TEMP%") do (
  if not exist "%%~D" mkdir "%%~D"
  if not exist "%%~D" exit /b 1
)
"%~dp0app\opencode.exe" %*
exit /b %errorlevel%
