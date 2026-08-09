[CmdletBinding()]
param(
    [string]$AgeExecutable,
    [string]$AgeKeygenExecutable,
    [string]$PythonCommand = "py"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\..\recovery-tool")).Path
$BuildRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dist = Join-Path $BuildRoot "dist"
$Build = Join-Path $BuildRoot "build"
$Venv = Join-Path $BuildRoot ".venv-build"
$OutputName = "RBF-Recovery-Tool-Windows.exe"
$Output = Join-Path $Dist $OutputName

if (-not $AgeExecutable) { $AgeExecutable = (Get-Command age.exe -ErrorAction Stop).Source }
if (-not $AgeKeygenExecutable) { $AgeKeygenExecutable = Join-Path (Split-Path -Parent $AgeExecutable) "age-keygen.exe" }
$AgeExecutable = (Resolve-Path $AgeExecutable).Path
$AgeKeygenExecutable = (Resolve-Path $AgeKeygenExecutable).Path
if (Test-Path $Build) { Remove-Item $Build -Recurse -Force }
if (Test-Path $Dist) { Remove-Item $Dist -Recurse -Force }
New-Item -ItemType Directory -Path $Dist | Out-Null
$Python = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $Python)) { & $PythonCommand -3.13 -m venv $Venv }
& $Python -m pip install --disable-pip-version-check -r (Join-Path $Root "requirements-build.lock")
if ($LASTEXITCODE -ne 0) { throw "Build dependencies could not be installed." }
$env:RBF_AGE_EXE = $AgeExecutable
$env:RBF_AGE_KEYGEN_EXE = $AgeKeygenExecutable
$env:RBF_OUTPUT_NAME = "RBF-Recovery-Tool-Windows"
$env:RBF_CONSOLE = "0"
& $Python -m PyInstaller --noconfirm --clean --distpath $Dist --workpath $Build (Join-Path $Root "rbf-recovery-tool.spec")
if (-not (Test-Path $Output)) { throw "Build output is missing: $Output" }
$Hash = (Get-FileHash $Output -Algorithm SHA256).Hash.ToLowerInvariant()
"$Hash  $OutputName" | Set-Content -LiteralPath "$Output.sha256" -Encoding ascii
Write-Host "Built $Output"

