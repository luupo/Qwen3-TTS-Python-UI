@echo off
title Qwen3-TTS Voice Clone
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python voice_clone_ui.py
if errorlevel 1 (
    echo.
    echo Fehler beim Start. Pruefe: Python 3.10+ installiert? Abhaengigkeiten mit "pip install -r requirements.txt" installiert?
    pause
)
