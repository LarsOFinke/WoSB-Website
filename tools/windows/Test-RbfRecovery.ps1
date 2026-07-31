[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Bundle,
    [Parameter(Mandatory = $true)][string]$Identity
)

$ErrorActionPreference = "Stop"
$age = Get-Command age -ErrorAction SilentlyContinue
if (-not $age) {
    throw "age wurde nicht gefunden. Installiere es z. B. mit: winget install FiloSottile.age"
}
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python wurde nicht gefunden. Installiere Python 3 für die sichere Archiv- und Manifestprüfung."
}
if (-not (Test-Path -LiteralPath $Bundle)) { throw "Bundle fehlt: $Bundle" }
if (-not (Test-Path -LiteralPath $Identity)) { throw "Identität fehlt: $Identity" }

$checksumPath = "$Bundle.sha256"
if (-not (Test-Path -LiteralPath $checksumPath)) {
    throw "Prüfsummendatei fehlt: $checksumPath"
}
$expected = ((Get-Content -LiteralPath $checksumPath -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$actual = (Get-FileHash -LiteralPath $Bundle -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expected -ne $actual) { throw "SHA-256-Prüfsumme des Bundles stimmt nicht überein." }

$bundleTool = Resolve-Path (Join-Path $PSScriptRoot "..\..\infrastructure\scripts\backup\recovery_bundle.py")
$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("rbf-recovery-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    $archive = Join-Path $temp "recovery.tar.gz"
    $extracted = Join-Path $temp "extracted"

    & $age.Source -d -i $Identity -o $archive $Bundle
    if ($LASTEXITCODE -ne 0) { throw "Das Recovery-Bundle konnte nicht entschlüsselt werden." }

    $manifestJson = & $python.Source $bundleTool.Path extract-and-verify $archive $extracted
    if ($LASTEXITCODE -ne 0) { throw "Sichere Archiv- oder Manifestprüfung ist fehlgeschlagen." }
    $manifest = $manifestJson | ConvertFrom-Json

    Write-Host "Recovery-Bundle vollständig geprüft."
    Write-Host "Erstellt: $($manifest.created_at)"
    Write-Host "Version: $($manifest.application.version)"
    Write-Host "Manifest-Dateien: $($manifest.files.Count)"
}
finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
