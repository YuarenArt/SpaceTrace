param([string]$QgisRoot = "F:\QGIS")

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
$taskDir = Join-Path $tempRoot ("spacetrace-pytest-" + [guid]::NewGuid().ToString("N"))
$taskFull = [IO.Path]::GetFullPath($taskDir)
if (-not $taskFull.StartsWith($tempRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw "Temporary path escaped the system temp directory: $taskFull"
}

$exitCode = 1
try {
    New-Item -ItemType Directory -Path $taskFull | Out-Null
    $env:QT_QPA_PLATFORM = "offscreen"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    Push-Location $repo
    try {
        & (Join-Path $QgisRoot "bin\python-qgis-ltr.bat") -m pytest -q `
            --basetemp (Join-Path $taskDir "pytest") `
            --benchmark-storage (Join-Path $taskDir "benchmarks") test
        $exitCode = $LASTEXITCODE
    }
    finally { Pop-Location }
}
finally {
    if (Test-Path -LiteralPath $taskFull) {
        $resolved = [IO.Path]::GetFullPath($taskFull)
        if (-not $resolved.StartsWith($tempRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing cleanup outside system temp: $resolved"
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
exit $exitCode
