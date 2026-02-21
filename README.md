# Qwen3-TTS Voice Clone – Windows UI

A simple desktop tool for **voice cloning** with [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS): provide reference audio (3–30 sec) and transcript, load the model, and generate any text in the cloned voice.

---

## Quick start

```powershell
cd QwenTTSWindows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip && pip install -r requirements.txt
python voice_clone_ui.py
```

Or after installation: **double-click `start.bat`** (uses `.venv` automatically if present).

---

## Requirements

| Item | Details |
|------|---------|
| **OS** | Windows 10/11 |
| **Python** | 3.10 or newer (3.12 recommended) |
| **GPU** | NVIDIA with CUDA recommended (faster); runs on CPU only as well |
| **Optional** | Flash Attention 2 (less VRAM), ffmpeg (for MP3 export & Whisper with non-WAV) |

---

## Installation (including other machines)

Same steps for **first-time setup** and for **running on another PC**.

1. **Project folder**  
   Have the `QwenTTSWindows` folder with all files (e.g. copy or clone the repo).

2. **Python 3.10+**  
   If needed: [python.org](https://www.python.org/downloads/) or `winget install Python.Python.3.12`. Enable **“Add Python to PATH”** during setup.

3. **Virtual environment (recommended)**  
   In the project folder:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   Before each run: activate the venv (see above) or use `start.bat`.

4. **Dependencies**  
   ```powershell
   pip install -U pip
   pip install -r requirements.txt
   ```
   This installs **CPU-only PyTorch**. On first generation the app downloads the model from Hugging Face (one-time, several GB).

5. **Optional: GPU (NVIDIA)**  
   For faster generation and GPU usage:
   ```powershell
   pip uninstall -y torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```
   Other CUDA builds: [pytorch.org/get-started/locally](https://pytorch.org/get-started/locally/) (e.g. cu124, cu128).

6. **Optional: Check environment**  
   ```powershell
   python check_setup.py
   ```
   Shows Python, PyTorch, CUDA status and missing packages.

7. **Optional: Flash Attention 2** (less VRAM)  
   ```powershell
   pip install -U flash-attn --no-build-isolation
   ```
   Then enable “Flash Attention 2” in the UI.

**Notes:**  
- **MP3 / Whisper for non-WAV:** ffmpeg in PATH (e.g. `winget install Gyan.FFmpeg`).  
- **WAV only:** Transcription and export work without ffmpeg.

---

## Run

- **Double-click:** `start.bat` (activates `.venv` if present and starts the app).
- **Command line:**  
  After activating the venv: `python voice_clone_ui.py`.

---

## Using the app

1. **Model** – Enter a local model folder or pick a preset (0.6B / 1.7B Base) → **Load model**.
2. **Reference audio** – Choose a WAV file (3–30 sec) via **File…**.
3. **Transcript** – Enter the exact spoken text of the reference (important for clone quality). Optional: **Transcribe with Whisper**.
4. **Text to speak** – Enter the output text you want in the cloned voice.
5. **Language** – Select target language or “Auto”.
6. **Export** – WAV or MP3; set output path (default: `Documents\QwenTTS_Output\`).
7. **▶ Start – Clone voice & generate audio** – Start generation.

The UI is available in **German** and **English** (default follows Windows language).

---

## Project layout

| File | Description |
|------|-------------|
| `voice_clone_ui.py` | Main UI (CustomTkinter) |
| `tts_backend.py` | Qwen3-TTS backend (load, generate, Whisper) |
| `ui_lang.py` | UI translations (DE/EN) |
| `requirements.txt` | Python dependencies (incl. CPU/GPU note) |
| `start.bat` / `start.ps1` | Double-click launcher |
| `check_setup.py` | Environment check (`python check_setup.py`) |

Default output folder: `Documents\QwenTTS_Output\`.

---

## License / Credits

[Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) (Apache-2.0) – Alibaba Cloud / Qwen Team.
