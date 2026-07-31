[CmdletBinding()]
param(
    [string]$AgeExecutable,
    [string]$AgeKeygenExecutable,
    [string]$PythonCommand = "py"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$CommonRoot = (Resolve-Path (Join-Path $Root "..\..\recovery-tool")).Path
Set-Location $Root

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
if (-not (Test-Path $AgeKeygenExecutable)) {
    throw "age-keygen.exe wurde nicht neben age.exe gefunden. Übergib -AgeKeygenExecutable C:\Pfad\age-keygen.exe."
}
$AgeKeygenExecutable = (Resolve-Path $AgeKeygenExecutable).Path
& $AgeKeygenExecutable --version | Out-Null
if ($LASTEXITCODE -ne 0) { throw "age-keygen.exe konnte nicht ausgeführt werden." }

$Venv = Join-Path $Root ".venv-build"
if (-not (Test-Path $Venv)) {
    & $PythonCommand -3.13 -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw "Python-Umgebung konnte nicht erstellt werden." }
}
$Python = Join-Path $Venv "Scripts\python.exe"
& $Python -m pip install --disable-pip-version-check --upgrade pip
& $Python -m pip install --disable-pip-version-check -r (Join-Path $CommonRoot "requirements-build.lock")

$env:RBF_AGE_EXE = $AgeExecutable
$env:RBF_AGE_KEYGEN_EXE = $AgeKeygenExecutable
$env:RBF_OUTPUT_NAME = "RBF-Recovery-Tool-Windows"
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath (Join-Path $Root "dist") `
    --workpath (Join-Path $Root "build") `
    (Join-Path $CommonRoot "rbf-recovery-tool.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller-Build ist fehlgeschlagen." }

$Output = Join-Path $Root "dist\RBF-Recovery-Tool-Windows.exe"
if (-not (Test-Path $Output)) { throw "Build-Ausgabe fehlt: $Output" }
$Hash = (Get-FileHash -LiteralPath $Output -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host ""
Write-Host "Fertig: $Output"
Write-Host "SHA-256: $Hash"
Write-Host "Auf dem Ziel-Laptop werden nur diese EXE und die private age-Identität benötigt."
