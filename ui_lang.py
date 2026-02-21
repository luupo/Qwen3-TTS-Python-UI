"""
UI-Sprachen: Deutsch (de) und Englisch (en).
Standard: Deutsch, wenn Windows auf Deutsch eingestellt ist, sonst Englisch.
"""
from __future__ import annotations

import sys

# Alle UI-Texte: key -> (de, en)
TEXTS = {
    "app_title": ("Qwen3-TTS Voice Clone", "Qwen3-TTS Voice Clone"),
    "main_title": ("Stimme klonen mit Qwen3-TTS", "Clone voice with Qwen3-TTS"),
    "model": ("Modell", "Model"),
    "model_dir_hint": (
        "Lokaler Modellordner (nur Base-Modell für Stimmenklon, z. B. …-Base; nicht CustomVoice). Leer = von Hugging Face laden:",
        "Local model folder (Base model for voice cloning only, e.g. …-Base; not CustomVoice). Empty = load from Hugging Face:",
    ),
    "browse_folder": ("Ordner wählen…", "Browse for folder…"),
    "download_path_hint": (
        "Speicherort für Modell-Downloads (wenn von Hugging Face geladen; leer = Standard-Cache):",
        "Model download location (when loading from Hugging Face; empty = default cache):",
    ),
    "or_preset": ("Oder Preset:", "Or preset:"),
    "preset_06": ("0.6B Base (schneller, weniger VRAM)", "0.6B Base (faster, less VRAM)"),
    "preset_17": ("1.7B Base (bessere Qualität)", "1.7B Base (better quality)"),
    "flash_attn": ("Flash Attention 2 (GPU, weniger VRAM)", "Flash Attention 2 (GPU, less VRAM)"),
    "load_model": ("Modell laden", "Load model"),
    "load_model_local": ("Modell laden (lokal)", "Load model (local)"),
    "model_status_default": (
        "Modell wird beim ersten Start automatisch geladen. Optional: vorher „Modell laden“ (bei lokalem Ordner oft 1–2 Min.).",
        "Model loads automatically on first run. Optional: click „Load model“ first (local folder often 1–2 min).",
    ),
    "device_cuda": ("Rechengerät: {device} (NVIDIA GPU – wird bei Generierung genutzt)", "Device: {device} (NVIDIA GPU – used for generation)"),
    "device_cpu": (
        "Rechengerät: CPU (keine GPU, daher 0 % GPU-Auslastung). Für GPU: PyTorch mit CUDA installieren (z. B. pip install torch --index-url https://download.pytorch.org/whl/cu121).",
        "Device: CPU (no GPU, so 0 % GPU usage). For GPU: install PyTorch with CUDA (e.g. pip install torch --index-url https://download.pytorch.org/whl/cu121).",
    ),
    "ref_audio": ("Referenz-Audio (3–30 Sek., WAV empfohlen)", "Reference audio (3–30 sec, WAV recommended)"),
    "file_btn": ("Datei…", "File…"),
    "play_btn": ("▶ Abspielen", "▶ Play"),
    "transcript_label": ("Transkript der Referenz-Audio (genau das, was gesprochen wird):", "Transcript of reference audio (exactly what is spoken):"),
    "transcribe_btn": ("Mit Whisper transkribieren", "Transcribe with Whisper"),
    "synth_label": ("Text zum Vorlesen (mit geklonter Stimme)", "Text to speak (with cloned voice)"),
    "language": ("Sprache:", "Language:"),
    "export_format": ("Export-Format:", "Export format:"),
    "output_file": ("Ausgabe-Datei:", "Output file:"),
    "save_as": ("Speichern unter…", "Save as…"),
    "start": ("Start", "Start"),
    "start_hint": ("Referenz-Audio und Transkript ausfüllen, Modell laden, dann hier starten.", "Fill reference audio and transcript, load model, then start here."),
    "btn_generate": ("▶  Start – Stimme klonen & Audio erzeugen", "▶  Start – Clone voice & generate audio"),
    "load_model_auto": ("(lädt Modell bei Bedarf automatisch)", "(loads model automatically if needed)"),
    "ffmpeg_hint": ("(ffmpeg erforderlich)", "(ffmpeg required)"),
    # Status / Buttons während Aktionen
    "loading": ("Laden…", "Loading…"),
    "starte": ("Starte …", "Starting …"),
    "model_loading": ("Modell wird geladen …", "Model loading …"),
    "model_loading_local": ("Modell wird geladen (lokal) …", "Model loading (local) …"),
    "model_loaded": ("Modell geladen.", "Model loaded."),
    "playing": ("Spielt …", "Playing …"),
    "transcribing": ("Transkribiere …", "Transcribing …"),
    "transcribe_done": ("Fertig.", "Done."),
    "generating": ("Generierung läuft …", "Generation running …"),
    "generating_load": ("Modell wird geladen …", "Model loading …"),
    "generating_then": ("Modell wird geladen, danach startet die Generierung …", "Model loading, then generation will start …"),
    "generating_pct": ("Generiere Audio … {p} %", "Generating audio … {p} %"),
    "saved": ("Gespeichert: {path}", "Saved: {path}"),
    "error_prefix": ("Fehler: {msg}", "Error: {msg}"),
    # Dialoge
    "dlg_ref_audio": ("Referenz-Audio wählen", "Choose reference audio"),
    "dlg_model_dir": ("TTS-Modellordner wählen", "Choose TTS model folder"),
    "dlg_download_dir": ("Speicherort für Modell-Downloads wählen", "Choose model download location"),
    "dlg_save_as": ("Ausgabe speichern unter", "Save output as"),
    "dlg_play": ("Abspielen", "Play"),
    "dlg_transcript": ("Transkript", "Transcript"),
    "dlg_input": ("Eingabe", "Input"),
    "dlg_load_model": ("Modell laden", "Load model"),
    "dlg_generation": ("Generierung", "Generation"),
    "dlg_done": ("Fertig", "Done"),
    "dlg_model_type": ("Modelltyp", "Model type"),
    # Meldungen
    "warn_ref_audio": ("Bitte zuerst eine gültige Referenz-Audiodatei wählen.", "Please select a valid reference audio file first."),
    "warn_transcript": ("Bitte das Transkript der Referenz-Audio eingeben.", "Please enter the transcript of the reference audio."),
    "warn_text": ("Bitte den zu sprechenden Text eingeben.", "Please enter the text to be spoken."),
    "warn_output": ("Bitte einen Ausgabe-Dateipfad angeben.", "Please specify an output file path."),
    "confirm_custom_voice": (
        "Der gewählte Ordner klingt nach dem CustomVoice-Modell.\n\nFür Stimmenklon wird das Base-Modell benötigt (z. B. Qwen3-TTS-12Hz-1.7B-Base).\nTrotzdem versuchen?",
        "The selected folder sounds like the CustomVoice model.\n\nVoice cloning requires the Base model (e.g. Qwen3-TTS-12Hz-1.7B-Base).\nTry anyway?",
    ),
    "error_load_model": ("Modell konnte nicht geladen werden:\n{err}", "Failed to load model:\n{err}"),
    "error_transcribe": ("Transkription fehlgeschlagen:\n{err}", "Transcription failed:\n{err}"),
    "error_generate": ("Fehler bei der Generierung:\n{msg}", "Generation error:\n{msg}"),
    "info_saved": ("Audio wurde gespeichert unter:\n{path}", "Audio saved to:\n{path}"),
    "restart_for_lang": ("Sprache wird nach Neustart der App übernommen.", "Language will apply after restarting the app."),
    # UI-Sprache Auswahl
    "ui_language_label": ("Sprache der Oberfläche:", "UI language:"),
    "ui_lang_de": ("Deutsch", "German"),
    "ui_lang_en": ("English", "English"),
    # Geschwindigkeit / Stil / Emotion
    "speed_label": ("Sprechgeschwindigkeit:", "Speech speed:"),
    "speed_hint": ("1.0 = normal, <1 langsamer, >1 schneller (nachträglich)", "1.0 = normal, <1 slower, >1 faster (post-processing)"),
    "temperature_label": ("Variation / Temperatur:", "Variation / temperature:"),
    "temperature_hint": ("höher = variabler; Standard 0.9", "higher = more varied; default 0.9"),
}
# Platzhalter für Textboxen (werden nur bei DE/EN gesetzt)
REF_PLACEHOLDER = ("Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it!", "Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it!")
SYNTH_PLACEHOLDER_DE = "Hallo! Das ist ein Test der geklonten Stimme."
SYNTH_PLACEHOLDER_EN = "Hello! This is a test of the cloned voice."


def get_default_ui_locale() -> str:
    """
    Standard-UI-Sprache: Deutsch, wenn Windows auf Deutsch steht, sonst Englisch.
    """
    if sys.platform != "win32":
        try:
            import locale
            loc, _ = locale.getlocale()
            if loc and (loc.startswith("de") or (isinstance(loc, tuple) and loc[0] and loc[0].startswith("de"))):
                return "de"
        except Exception:
            pass
        return "en"
    try:
        ctypes = __import__("ctypes")
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        lang_id = kernel32.GetUserDefaultUILanguage()
        # Primäre Sprach-ID: untere 10 Bit; Deutsch = 0x07
        if (lang_id & 0x3FF) == 0x07:
            return "de"
    except Exception:
        pass
    return "en"


def get_text(lang: str, key: str, **fmt) -> str:
    """Übersetzung für key in lang (de/en). fmt für .format()."""
    if lang not in ("de", "en"):
        lang = "en"
    entry = TEXTS.get(key)
    if not entry:
        return key
    text = entry[0] if lang == "de" else entry[1]
    if fmt:
        try:
            text = text.format(**fmt)
        except KeyError:
            pass
    return text
