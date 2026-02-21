# Qwen3-TTS Voice Clone – Windows-UI

Einfaches Desktop-Tool zum **Stimmenklonen** mit [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS): Referenz-Audio (3–30 Sek.) + Transkript eingeben, Modell laden, beliebigen Text in der geklonten Stimme generieren.

---

## Schnellstart

```powershell
cd QwenTTSWindows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip && pip install -r requirements.txt
python voice_clone_ui.py
```

Oder nach der Installation: **Doppelklick auf `start.bat`** (nutzt automatisch `.venv`, falls vorhanden).

---

## Voraussetzungen

| Was | Details |
|-----|--------|
| **Betriebssystem** | Windows 10/11 |
| **Python** | 3.10 oder neuer (empfohlen: 3.12) |
| **GPU** | NVIDIA mit CUDA empfohlen (schneller); läuft auch nur auf CPU |
| **Optional** | Flash Attention 2 (weniger VRAM), ffmpeg (für MP3-Export & Whisper bei Nicht-WAV) |

---

## Installation (inkl. anderer Rechner)

Gleicher Ablauf für **Erstinstallation** und für **„auf einem anderen Rechner starten“**.

1. **Projektordner**  
   Ordner `QwenTTSWindows` mit allen Dateien (z. B. per Kopie oder Clone) bereitstellen.

2. **Python 3.10+**  
   Falls nötig: [python.org](https://www.python.org/downloads/) oder `winget install Python.Python.3.12`. Bei der Installation **„Add Python to PATH“** aktivieren.

3. **Virtuelle Umgebung (empfohlen)**  
   Im Projektordner:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   Vor jedem späteren Start: venv aktivieren (siehe oben) oder `start.bat` verwenden.

4. **Abhängigkeiten**  
   ```powershell
   pip install -U pip
   pip install -r requirements.txt
   ```
   Das installiert **PyTorch für CPU**. Beim ersten Generieren lädt die App das Modell von Hugging Face (einmalig, mehrere GB).

5. **Optional: GPU (NVIDIA)**  
   Für schnellere Generierung und GPU-Auslastung:
   ```powershell
   pip uninstall -y torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```
   Andere CUDA-Varianten: [pytorch.org/get-started/locally](https://pytorch.org/get-started/locally/) (z. B. cu124, cu128).

6. **Optional: Umgebung prüfen**  
   ```powershell
   python check_setup.py
   ```
   Zeigt Python, PyTorch, CUDA-Status und fehlende Pakete.

7. **Optional: Flash Attention 2** (weniger VRAM)  
   ```powershell
   pip install -U flash-attn --no-build-isolation
   ```
   In der UI dann „Flash Attention 2“ aktivieren.

**Kurz-Hinweise:**  
- **MP3 / Whisper für Nicht-WAV:** ffmpeg im PATH (z. B. `winget install Gyan.FFmpeg`).  
- **Nur WAV:** Transkription und Export funktionieren ohne ffmpeg.

---

## Start

- **Doppelklick:** `start.bat` (aktiviert ggf. `.venv` und startet die App).
- **Kommandozeile:**  
  Nach Aktivierung der venv: `python voice_clone_ui.py`.

---

## Nutzung in der App

1. **Modell** – Lokalen Modellordner angeben oder Preset (0.6B / 1.7B Base) wählen → **Modell laden**.
2. **Referenz-Audio** – WAV (3–30 Sek.) über **Datei…** wählen.
3. **Transkript** – Genau den gesprochenen Text der Referenz-Audio eintragen (wichtig für Klonqualität). Optional: **Mit Whisper transkribieren**.
4. **Text zum Vorlesen** – Den gewünschten Ausgabetext eingeben.
5. **Sprache** – Zielsprache oder „Auto“ wählen.
6. **Export** – WAV oder MP3; Ausgabepfad setzen (Standard: `Documents\QwenTTS_Output\`).
7. **▶ Start – Stimme klonen & Audio erzeugen** – Generierung starten.

---

## Projektstruktur

| Datei | Beschreibung |
|-------|--------------|
| `voice_clone_ui.py` | Haupt-UI (CustomTkinter) |
| `tts_backend.py` | Qwen3-TTS-Anbindung (Laden, Generierung, Whisper) |
| `requirements.txt` | Python-Abhängigkeiten (inkl. Hinweis CPU/GPU) |
| `start.bat` / `start.ps1` | Start per Doppelklick |
| `check_setup.py` | Umgebungsprüfung (`python check_setup.py`) |

Ausgabe standardmäßig: `Documents\QwenTTS_Output\`.

---

## Lizenz / Danksagung

[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) (Apache-2.0) – Alibaba Cloud / Qwen Team.
