"""
Kurze Prüfung der Umgebung für Qwen3-TTS Voice Clone.
Aufruf: python check_setup.py
Nützlich vor dem ersten Start auf einem neuen Rechner.
"""
from __future__ import annotations

import sys

def main():
    print("=== Qwen3-TTS Voice Clone – Umgebungsprüfung ===\n")

    # Python
    py_ver = sys.version_info
    ok = py_ver >= (3, 10)
    print(f"Python: {sys.version.split()[0]}  {'OK (3.10+)' if ok else 'HINWEIS: Python 3.10+ empfohlen'}")

    # Pfad (Skriptordner)
    try:
        from pathlib import Path
        project_dir = Path(__file__).resolve().parent
        print(f"Projektordner: {project_dir}")
    except Exception:
        pass

    missing = []

    # PyTorch
    try:
        import torch
        cuda = torch.cuda.is_available()
        print(f"PyTorch: {torch.__version__}  {'(CUDA/GPU)' if cuda else '(CPU – für GPU siehe README)'}")
        if cuda:
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("PyTorch: NICHT INSTALLIERT  -> pip install -r requirements.txt")
        missing.append("torch")

    # Wichtige Pakete
    for name, mod in [
        ("customtkinter", "customtkinter"),
        ("soundfile", "soundfile"),
        ("sounddevice", "sounddevice"),
        ("qwen_tts", "qwen_tts"),
    ]:
        try:
            __import__(mod)
            print(f"{name}: OK")
        except ImportError:
            print(f"{name}: FEHLT")
            missing.append(name)

    # Optional
    try:
        __import__("whisper")
        print("openai-whisper: OK (Transkription)")
    except ImportError:
        print("openai-whisper: FEHLT (Transkription nicht möglich)")
        missing.append("openai-whisper")

    print()
    if missing:
        print("Fehlende Pakete installieren:")
        print("  pip install -r requirements.txt")
        print()
        return 1

    print("Umgebung OK. Start mit: python voice_clone_ui.py  oder  start.bat")
    return 0

if __name__ == "__main__":
    sys.exit(main())
