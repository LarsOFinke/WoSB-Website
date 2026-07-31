[CmdletBinding()]
param(
    [string]$Destination = "$HOME\RBF-Recovery"
)

$ErrorActionPreference = "Stop"
$ageKeygen = Get-Command age-keygen -ErrorAction SilentlyContinue
if (-not $ageKeygen) {
    throw "age-keygen wurde nicht gefunden. Installiere age zuerst, z. B. mit: winget install FiloSottile.age"
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
$identity = Join-Path $Destination "rbf-recovery-identity.txt"
$recipientFile = Join-Path $Destination "rbf-recovery-recipient.txt"
if (Test-Path $identity) {
    throw "Die Identitätsdatei existiert bereits: $identity"
}

& $ageKeygen.Source -o $identity
if ($LASTEXITCODE -ne 0) {
    throw "age-keygen konnte die Identität nicht erzeugen."
}
$recipient = (& $ageKeygen.Source -y $identity).Trim()
if ($LASTEXITCODE -ne 0 -or -not $recipient.StartsWith("age1")) {
    throw "Der öffentliche age-Empfänger konnte nicht ermittelt werden."
}
Set-Content -Path $recipientFile -Value $recipient -Encoding ascii -NoNewline

# Limit access to the current Windows account. The command may print localized status text.
& icacls $identity /inheritance:r /grant:r "$env:USERNAME`:(R,W)" | Out-Null
& icacls $recipientFile /inheritance:r /grant:r "$env:USERNAME`:(R,W)" | Out-Null

Write-Host "Recovery-Schlüssel erstellt."
Write-Host "Private Identität (niemals auf dem Pi speichern): $identity"
Write-Host "Öffentlicher Empfänger für BACKUP_AGE_RECIPIENT:"
Write-Host $recipient
