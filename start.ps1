# Qwen3-TTS Voice Clone – Start (PowerShell)
Set-Location $PSScriptRoot

if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

python voice_clone_ui.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Fehler beim Start. Pruefe: Python 3.10+ installiert? Abhaengigkeiten mit 'pip install -r requirements.txt' installiert?"
    Read-Host "Enter druecken zum Beenden"
}
