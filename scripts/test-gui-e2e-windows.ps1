param(
    [string]$QgisRoot = "F:\QGIS",
    [ValidateSet("offline", "mock-api", "live")][string]$Mode = "offline"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
$taskDir = Join-Path $tempRoot ("spacetrace-e2e-" + [guid]::NewGuid().ToString("N"))
$taskFull = [IO.Path]::GetFullPath($taskDir)
if (-not $taskFull.StartsWith($tempRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw "Temporary path escaped the system temp directory: $taskFull"
}

try {
    $plugins = Join-Path $taskDir "profiles\test\python\plugins"
    New-Item -ItemType Directory -Path $plugins -Force | Out-Null
    New-Item -ItemType Junction -Path (Join-Path $plugins "SpaceTrace") -Target $repo | Out-Null
    $tle = @(
        "1 25544U 98067A   25087.72483446  .00032194  00000-0  56484-3 0  9999",
        "2 25544  51.6386 345.5386 0004029  59.5799 332.6073 15.50242233502686"
    )
    Set-Content -LiteralPath (Join-Path $taskDir "iss.txt") -Value $tle -Encoding Ascii
    $env:SPACETRACE_E2E_DIR = $taskDir
    $env:SPACETRACE_LOG_PATH = Join-Path $taskDir "plugin.log"
    $env:QT_QPA_PLATFORM = "offscreen"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    $env:QGIS_PLUGINPATH = $plugins
    $env:SPACETRACE_REPO_ROOT = $repo
    $env:SPACETRACE_E2E_MODE = $Mode

    if ($Mode -eq "live") {
        & (Join-Path $repo "scripts\spacetrack-credentials-windows.ps1") -Action status -QgisRoot $QgisRoot
        if ($LASTEXITCODE -ne 0) { throw "SpaceTrack credentials are missing from the system keyring" }
    }

    $launcher = Join-Path $taskDir "launch.cmd"
    $startupFile = if ($Mode -eq "offline") { "qgis_startup.py" } else { "qgis_spacetrack_startup.py" }
    $startup = Join-Path $repo (Join-Path "test\e2e" $startupFile)
    $cmdText = @"
@echo off
call "$QgisRoot\bin\o4w_env.bat"
path %OSGEO4W_ROOT%\apps\qgis-ltr\bin;%PATH%
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/qgis-ltr
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qgis-ltr\qtplugins;%OSGEO4W_ROOT%\apps\qt5\plugins
"%OSGEO4W_ROOT%\bin\qgis-ltr-bin.exe" --nologo --profiles-path "$taskDir\profiles" --profile test --code "$startup"
"@
    Set-Content -LiteralPath $launcher -Value $cmdText -Encoding Ascii
    $process = Start-Process -FilePath $env:ComSpec -ArgumentList @('/d', '/c', ('"' + $launcher + '"')) -PassThru -WindowStyle Hidden
    $timeout = if ($Mode -eq "live") { 120000 } else { 90000 }
    if (-not $process.WaitForExit($timeout)) {
        Stop-Process -Id $process.Id -Force
        throw "QGIS E2E timed out after $($timeout / 1000) seconds"
    }
    $reportPath = Join-Path $taskDir "result.json"
    if (-not (Test-Path -LiteralPath $reportPath)) { throw "QGIS did not write an E2E result (exit $($process.ExitCode))" }
    $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    if (-not $report.ok) { throw $report.error }
    if ($Mode -eq "offline") {
        $reopenStartup = Join-Path $repo "test\e2e\qgis_reopen_startup.py"
        $reopenLauncher = Join-Path $taskDir "reopen.cmd"
        $reopenCommand = $cmdText.Replace($startup, $reopenStartup)
        Set-Content -LiteralPath $reopenLauncher -Value $reopenCommand -Encoding Ascii
        $reopenProcess = Start-Process -FilePath $env:ComSpec -ArgumentList @('/d', '/c', ('"' + $reopenLauncher + '"')) -PassThru -WindowStyle Hidden
        if (-not $reopenProcess.WaitForExit(90000)) {
            Stop-Process -Id $reopenProcess.Id -Force
            throw "QGIS project reopen timed out"
        }
        $reopenReportPath = Join-Path $taskDir "reopen_result.json"
        if (-not (Test-Path -LiteralPath $reopenReportPath)) { throw "QGIS did not write a project reopen result" }
        $reopenReport = Get-Content -LiteralPath $reopenReportPath -Raw | ConvertFrom-Json
        if (-not $reopenReport.ok) { throw $reopenReport.error }
        $report.scenarios += $reopenReport.scenarios
    }
    foreach ($scenario in $report.scenarios) {
        Write-Output ($scenario | ConvertTo-Json -Compress -Depth 4)
    }
    Write-Output "QGIS E2E: $($report.scenarios.Count) scenarios passed"
}
finally {
    if (Test-Path -LiteralPath $taskFull) {
        $resolved = [IO.Path]::GetFullPath($taskFull)
        if (-not $resolved.StartsWith($tempRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing cleanup outside system temp: $resolved"
        }
        $pluginLink = Join-Path $resolved "profiles\test\python\plugins\SpaceTrace"
        if (Test-Path -LiteralPath $pluginLink) {
            $linkItem = Get-Item -LiteralPath $pluginLink
            if (-not ($linkItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Refusing to remove a non-junction plugin path: $pluginLink"
            }
            # Windows PowerShell 5.1 Remove-Item can throw NullReferenceException
            # for a junction. Directory.Delete removes the link itself.
            [IO.Directory]::Delete($pluginLink)
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
