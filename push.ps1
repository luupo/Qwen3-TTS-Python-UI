# Commit und Push – Nutzung: .\push.ps1  oder  .\push.ps1 "Deine Nachricht"
# Verwendet .commit_msg.txt falls keine Nachricht uebergeben wird.

Set-Location $PSScriptRoot

$msg = $args[0]
$msgFile = Join-Path $PSScriptRoot ".commit_msg.txt"

if ($msg) {
    git add -A
    git status --short
    git commit -m $msg
} else {
    if (-not (Test-Path $msgFile)) {
        Write-Host "Fehler: .commit_msg.txt fehlt. Erstellen oder Aufruf: .\push.ps1 `"Deine Commit-Nachricht`""
        exit 1
    }
    git add -A
    git status --short
    git commit -F $msgFile
}

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git push origin master
