param(
    [ValidateSet("set", "status", "delete")][string]$Action = "status",
    [string]$QgisRoot = "F:\QGIS"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $QgisRoot "bin\python-qgis-ltr.bat"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "QGIS Python launcher was not found: $python"
}

# Windows PowerShell 5.1 can turn a native program's stderr into a terminating
# error when ErrorActionPreference is Stop. A missing import is expected here.
$ErrorActionPreference = "Continue"
& $python -c "import keyring" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Output "Installing keyring for QGIS Python..."
    & $python -m pip install --user keyring
    if ($LASTEXITCODE -ne 0) {
        throw "Could not install keyring for QGIS Python"
    }
    & $python -c "import keyring"
    if ($LASTEXITCODE -ne 0) {
        throw "keyring is still unavailable to QGIS Python after installation"
    }
}
& $python (Join-Path $repo "scripts\manage_spacetrack_credentials.py") $Action
exit $LASTEXITCODE
