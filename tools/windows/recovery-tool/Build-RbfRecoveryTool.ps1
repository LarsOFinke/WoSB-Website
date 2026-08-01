[CmdletBinding()]
param(
    [string]$AgeExecutable,
    [string]$AgeKeygenExecutable,
    [string]$PythonCommand = "py"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$CommonRoot = (Resolve-Path (Join-Path $Root "..\..\recovery-tool")).Path
$Dist = Join-Path $Root "dist"
$Build = Join-Path $Root "build"
$Venv = Join-Path $Root ".venv-build"
$OutputName = "RBF-Recovery-Tool-Windows.exe"
$Output = Join-Path $Dist $OutputName
Set-Location $Root

# dist and build contain generated output only. Reset them before prerequisite
# validation so an aborted rebuild cannot leave stale binaries behind.
if (Test-Path -LiteralPath $Build) { Remove-Item -LiteralPath $Build -Recurse -Force }
if (Test-Path -LiteralPath $Dist) { Remove-Item -LiteralPath $Dist -Recurse -Force }
New-Item -ItemType Directory -Path $Dist -Force | Out-Null

if (-not $AgeExecutable) {
    $age = Get-Command age.exe -ErrorAction SilentlyContinue
    if (-not $age) { $age = Get-Command age -ErrorAction SilentlyContinue }
    if (-not $age) {
        throw "age.exe wurde nicht gefunden. Installiere es auf dem Build-PC oder übergib -AgeExecutable C:\Pfad\age.exe."
    }
    $AgeExecutable = $age.Source
}
$AgeExecutable = (Resolve-Path $AgeExecutable).Path
& $AgeExecutable --version | Out-Null
if ($LASTEXITCODE -ne 0) { throw "age.exe konnte nicht ausgeführt werden." }

if (-not $AgeKeygenExecutable) {
    $AgeKeygenExecutable = Join-Path (Split-Path -Parent $AgeExecutable) "age-keygen.exe"
}
if (-not (Test-Path -LiteralPath $AgeKeygenExecutable -PathType Leaf)) {
    throw "age-keygen.exe wurde nicht neben age.exe gefunden. Übergib -AgeKeygenExecutable C:\Pfad\age-keygen.exe."
}
$AgeKeygenExecutable = (Resolve-Path $AgeKeygenExecutable).Path
& $AgeKeygenExecutable --version | Out-Null
if ($LASTEXITCODE -ne 0) { throw "age-keygen.exe konnte nicht ausgeführt werden." }

$Python = Join-Path $Venv "Scripts\python.exe"
if ((Test-Path -LiteralPath $Venv) -and -not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    Write-Host "Defekte Build-Umgebung wird neu erstellt: $Venv"
    Remove-Item -LiteralPath $Venv -Recurse -Force
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    if ($PythonCommand -eq "py") {
        & $PythonCommand -3.13 -m venv $Venv
    }
    else {
        & $PythonCommand -m venv $Venv
    }
    if ($LASTEXITCODE -ne 0) { throw "Python-Umgebung konnte nicht erstellt werden." }
}

& $Python -c "import sys; raise SystemExit(sys.version_info < (3, 11))"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 oder neuer ist für den Build erforderlich." }
& $Python -m pip install --disable-pip-version-check -r (Join-Path $CommonRoot "requirements-build.lock")
if ($LASTEXITCODE -ne 0) { throw "Build-Abhängigkeiten konnten nicht installiert werden." }

$env:PYTHONDONTWRITEBYTECODE = "1"
$env:RBF_AGE_EXE = $AgeExecutable
$env:RBF_AGE_KEYGEN_EXE = $AgeKeygenExecutable
$env:RBF_OUTPUT_NAME = "RBF-Recovery-Tool-Windows"
$env:RBF_CONSOLE = "0"
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath $Dist `
    --workpath $Build `
    (Join-Path $CommonRoot "rbf-recovery-tool.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller-Build ist fehlgeschlagen." }

if (-not (Test-Path -LiteralPath $Output -PathType Leaf)) { throw "Build-Ausgabe fehlt: $Output" }
$Hash = (Get-FileHash -LiteralPath $Output -Algorithm SHA256).Hash.ToLowerInvariant()
"$Hash  $OutputName" | Set-Content -LiteralPath "$Output.sha256" -Encoding ascii

Write-Host ""
Write-Host "Fertig: $Output"
Write-Host "SHA-256: $Hash"
Write-Host "Alle erzeugten Dateien liegen unter $Dist und sind nicht für Git vorgesehen."
