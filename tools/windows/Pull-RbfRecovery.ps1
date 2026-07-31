[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Server,
    [Parameter(Mandatory = $true)][string]$RemoteDirectory,
    [string]$Destination = "$HOME\RBF-Recovery\Backups",
    [string]$Identity = "$HOME\RBF-Recovery\rbf-recovery-identity.txt",
    [int]$Port = 22,
    [switch]$SkipContentVerification
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $Destination | Out-Null

$remoteCommand = "find '$RemoteDirectory' -maxdepth 1 -type f -name 'rbf-recovery-*.tar.gz.age' -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-"
$remoteFile = (& ssh -p $Port $Server $remoteCommand).Trim()
if ($LASTEXITCODE -ne 0 -or -not $remoteFile) {
    throw "Kein Recovery-Bundle im Remote-Verzeichnis gefunden: $RemoteDirectory"
}

$fileName = Split-Path -Leaf $remoteFile
$localBundle = Join-Path $Destination $fileName
$localChecksum = "$localBundle.sha256"
$remoteSpec = "${Server}:$remoteFile"
$remoteChecksumSpec = "${Server}:$remoteFile.sha256"

& scp -P $Port $remoteSpec $localBundle
if ($LASTEXITCODE -ne 0) { throw "Recovery-Bundle konnte nicht kopiert werden." }
& scp -P $Port $remoteChecksumSpec $localChecksum
if ($LASTEXITCODE -ne 0) { throw "Prüfsummendatei konnte nicht kopiert werden." }

$expected = ((Get-Content -LiteralPath $localChecksum -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$actual = (Get-FileHash -LiteralPath $localBundle -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expected -ne $actual) { throw "SHA-256-Prüfung nach SCP ist fehlgeschlagen." }
Write-Host "Recovery-Bundle kopiert und SHA-256 geprüft: $localBundle"

if (-not $SkipContentVerification) {
    if (-not (Test-Path -LiteralPath $Identity)) {
        throw "Private age-Identität fehlt für die Inhaltsprüfung: $Identity"
    }
    & (Join-Path $PSScriptRoot "Test-RbfRecovery.ps1") -Bundle $localBundle -Identity $Identity
}
