"""
Voice-Clone-Backend mit Qwen3-TTS Base-Modell.
Lädt das Modell einmal und bietet generate_voice_clone() für die UI.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

import torch


def get_default_device() -> str:
    """'cuda:0' wenn GPU verfügbar, sonst 'cpu'."""
    return "cuda:0" if torch.cuda.is_available() else "cpu"


def get_device_info() -> tuple[str, bool]:
    """
    Returns: (device_name, cuda_available).
    Für UI-Anzeige: ob GPU genutzt wird oder nur CPU (dann ist GPU bei 0 %).
    """
    cuda_ok = torch.cuda.is_available()
    device = "cuda:0" if cuda_ok else "cpu"
    return (device, cuda_ok)


def load_model(
    model_name: str = "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    device: Optional[str] = None,
    use_flash_attn: bool = False,
    cache_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
):
    """
    Lädt das Qwen3-TTS Base-Modell für Voice Cloning.
    progress_callback(progress 0..1, message) wird bei Fortschritt aufgerufen (Download oder Lade-Phasen).
    """
    from qwen_tts import Qwen3TTSModel

    device = device or get_default_device()
    dtype = torch.bfloat16 if device.startswith("cuda") else torch.float32
    attn = "flash_attention_2" if (use_flash_attn and device.startswith("cuda")) else "eager"

    kwargs = dict(
        device_map=device,
        dtype=dtype,
        attn_implementation=attn,
    )
    if cache_dir and os.path.isdir(cache_dir):
        kwargs["cache_dir"] = cache_dir

    is_local = os.path.isdir(model_name) or (
        not (model_name.startswith("Qwen/") or model_name.startswith("http")) and os.path.isdir(model_name)
    )

    def report(p: float, msg: str) -> None:
        if progress_callback:
            progress_callback(p, msg)

    report(0.0, "Lade Modell …")

    # Bei Download von Hugging Face: tqdm abfangen für echten Fortschritt
    if not is_local and progress_callback:
        try:
            import huggingface_hub.file_download as hf_fd
            _orig_tqdm = getattr(hf_fd, "tqdm", None)
            if _orig_tqdm is None:
                import tqdm.auto as tqdm_auto
                _orig_tqdm = tqdm_auto.tqdm

            class _ProgressTqdm(_orig_tqdm):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self._report = report
                def update(self, n=1):
                    super().update(n)
                    total = getattr(self, "total", None)
                    if total and total > 0:
                        p = self.n / total
                        self._report(min(0.95, p), "Lade Dateien …")

            hf_fd.tqdm = _ProgressTqdm
            try:
                model = Qwen3TTSModel.from_pretrained(model_name, **kwargs)
            finally:
                hf_fd.tqdm = _orig_tqdm
        except Exception:
            model = Qwen3TTSModel.from_pretrained(model_name, **kwargs)
    else:
        # Lokal: kurze Phase „Dateien prüfen“, dann Laden (kein Feingranularer Fortschritt)
        if is_local and progress_callback:
            _ = list(Path(model_name).iterdir())  # Dateien sichtbar machen
            report(0.1, "Lade Gewichte …")
        model = Qwen3TTSModel.from_pretrained(model_name, **kwargs)

    report(1.0, "Fertig")
    return model


def _ensure_extension(path: str, fmt: str) -> Path:
    """Stellt sicher, dass path die richtige Endung für fmt hat."""
    p = Path(path)
    ext = ".wav" if fmt.lower() == "wav" else ".mp3"
    if p.suffix.lower() != ext:
        p = p.with_suffix(ext)
    return p


def _find_ffmpeg() -> Optional[str]:
    """Sucht ffmpeg im PATH oder in typischen Windows-Installationspfaden (z. B. WinGet)."""
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    # WinGet (Gyan.FFmpeg) z. B. unter LocalAppData\...\Packages\Gyan.FFmpeg_...\ffmpeg-*-full_build\bin\ffmpeg.exe
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        winget = Path(local) / "Microsoft" / "WinGet" / "Packages"
        if winget.is_dir():
            for pkg in winget.iterdir():
                if not pkg.is_dir() or "ffmpeg" not in pkg.name.lower() and "Gyan" not in pkg.name:
                    continue
                bin_ff = pkg / "bin" / "ffmpeg.exe"
                if bin_ff.is_file():
                    return str(bin_ff)
                for sub in pkg.iterdir():
                    if sub.is_dir() and "ffmpeg" in sub.name.lower():
                        bin_ff = sub / "bin" / "ffmpeg.exe"
                        if bin_ff.is_file():
                            return str(bin_ff)
                        break
    return None


def _apply_trailing_fade_and_silence(wav: "np.ndarray", sr: int) -> "np.ndarray":
    """
    Mildert abgehacktes Ende: letzte ~150 ms weich ausblenden, dann ~400 ms Stille.
    Reduziert harten Schnitt am Ende der Generierung.
    """
    import numpy as np
    if wav.ndim > 1:
        wav = wav[:, 0] if wav.shape[1] == 1 else wav.mean(axis=1)
    wav = np.asarray(wav, dtype=np.float32)
    n = len(wav)
    if n < 10:
        return wav
    fade_samples = min(int(0.2 * sr), n // 4)  # max. 200 ms ausblenden
    silence_samples = int(0.45 * sr)  # 450 ms Stille anhängen
    # Lineares Fade-Out auf den letzten fade_samples
    fade = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
    wav[-fade_samples:] = wav[-fade_samples:] * fade
    wav = np.concatenate([wav, np.zeros(silence_samples, dtype=np.float32)])
    return wav


def _apply_speed(wav: "np.ndarray", sr: int, speed: float) -> "np.ndarray":
    """
    Ändert die Abspielgeschwindigkeit ohne Tonhöhenänderung (time-stretch).
    speed > 1 = schneller, speed < 1 = langsamer.
    """
    if speed is None or abs(speed - 1.0) < 0.01:
        return wav
    import numpy as np
    import librosa
    if wav.ndim > 1:
        wav = wav[:, 0] if wav.shape[1] == 1 else wav.mean(axis=1)
    wav = np.asarray(wav, dtype=np.float32)
    # rate in librosa: >1 = schneller
    stretched = librosa.effects.time_stretch(wav, rate=float(speed))
    return stretched.astype(np.float32)


def _write_audio(wav: "np.ndarray", sr: int, output_path: Path, output_format: str) -> None:
    """
    Schreibt Audio in das gewählte Format (wav oder mp3).
    Für MP3 wird pydub genutzt (benötigt ffmpeg im PATH oder WinGet-Installation).
    """
    import numpy as np
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = output_format.lower()
    if fmt == "wav":
        import soundfile as sf
        sf.write(str(output_path), wav, sr)
        return
    if fmt == "mp3":
        try:
            from pydub import AudioSegment
        except ImportError:
            raise RuntimeError(
                "MP3-Export benötigt das Paket 'pydub'. Bitte installieren: pip install pydub"
            )
        ffmpeg_path = _find_ffmpeg()
        if ffmpeg_path:
            AudioSegment.converter = ffmpeg_path
            # ffprobe oft im selben Ordner
            ffprobe = Path(ffmpeg_path).parent / "ffprobe.exe"
            if ffprobe.is_file():
                AudioSegment.ffprobe = str(ffprobe)
        # Float32 [-1, 1] -> Int16 mono
        if wav.ndim > 1:
            wav = wav[:, 0]
        wav_int = (np.clip(wav, -1.0, 1.0) * 32767).astype(np.int16)
        segment = AudioSegment(
            data=wav_int.tobytes(),
            sample_width=2,
            frame_rate=sr,
            channels=1,
        )
        try:
            segment.export(str(output_path), format="mp3", bitrate="192k")
        except FileNotFoundError:
            raise FileNotFoundError(
                "MP3-Export benötigt ffmpeg. Bitte ffmpeg installieren und in die PATH-Umgebungsvariable aufnehmen.\n"
                "Download: https://ffmpeg.org/download.html (z. B. Windows Builds von gyan.dev)"
            )
        except OSError as e:
            if getattr(e, "winerror", None) == 2 or "ffmpeg" in str(e).lower() or "cannot find" in str(e).lower():
                raise FileNotFoundError(
                    "MP3-Export benötigt ffmpeg. ffmpeg wurde nicht gefunden (nicht im PATH?).\n"
                    "Bitte ffmpeg installieren: https://ffmpeg.org/download.html"
                ) from e
            raise
        return
    raise ValueError(f"Unbekanntes Export-Format: {output_format}")


def generate_voice_clone(
    model,
    text: str,
    language: str,
    ref_audio_path: str,
    ref_text: str,
    output_path: str,
    output_format: str = "wav",
    x_vector_only_mode: bool = False,
    speed: float = 1.0,
    temperature: Optional[float] = None,
) -> tuple[str, Optional[str]]:
    """
    Generiert Audio mit geklonter Stimme.
    output_format: "wav" oder "mp3" (mp3 erfordert pydub + ffmpeg).
    speed: Abspielgeschwindigkeit (1.0 = normal, >1 schneller, <1 langsamer).
    temperature: Sampling-Temperatur (z. B. 0.7–1.0); höher = variabler/emotionaler.
    Returns: (output_path, error_message). error_message ist None bei Erfolg.
    """
    try:
        gen_kwargs = {}
        if temperature is not None:
            gen_kwargs["temperature"] = float(temperature)
        wavs, sr = model.generate_voice_clone(
            text=text,
            language=language,
            ref_audio=ref_audio_path,
            ref_text=ref_text,
            x_vector_only_mode=x_vector_only_mode,
            **gen_kwargs,
        )
        wav = wavs[0]
        wav = _apply_trailing_fade_and_silence(wav, sr)
        wav = _apply_speed(wav, sr, speed)
        out = _ensure_extension(output_path, output_format)
        _write_audio(wav, sr, out, output_format)
        return (str(out.resolve()), None)
    except Exception as e:
        return ("", str(e))


def _load_audio_for_whisper(audio_path: str) -> tuple["np.ndarray", bool]:
    """
    Lädt Audio ohne ffmpeg (vermeidet WinError 2 unter Windows).
    Verwendet soundfile für WAV/FLAC/OGG; bei anderen Formaten wird ffmpeg gesucht.
    Returns: (audio_16k_mono_float32, used_ffmpeg_path).
    """
    import numpy as np
    path = Path(audio_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Audiodatei nicht gefunden: {audio_path}")

    suf = path.suffix.lower()
    # soundfile unterstützt WAV, FLAC, OGG etc. – kein ffmpeg nötig
    if suf in (".wav", ".flac", ".ogg", ".oga"):
        import soundfile as sf
        data, sr = sf.read(str(path), dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
    else:
        # MP3/andere: ffmpeg in PATH setzen, dann Whisper-interne Ladung nutzen
        ffmpeg_path = _find_ffmpeg()
        if not ffmpeg_path:
            raise FileNotFoundError(
                f"Für das Format '{suf}' wird ffmpeg benötigt. Bitte ffmpeg installieren "
                "(z. B. winget install Gyan.FFmpeg) und in PATH aufnehmen."
            )
        ffmpeg_dir = str(Path(ffmpeg_path).parent)
        path_env = os.environ.get("PATH", "")
        if ffmpeg_dir not in path_env:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + path_env
        import whisper
        data = whisper.load_audio(str(path))
        return (data, True)

    # Auf 16 kHz Mono resamplen (Whisper erwartet 16 kHz)
    if sr != 16000:
        import librosa
        data = librosa.resample(data, orig_sr=sr, target_sr=16000)
    return (data.astype("float32"), False)


def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> tuple[str, Optional[str]]:
    """
    Transkribiert Audio mit OpenAI Whisper.
    Lädt Audio mit soundfile (kein ffmpeg nötig für WAV/FLAC/OGG), um WinError 2 zu vermeiden.
    model_size: "tiny", "base", "small", "medium", "large".
    progress_callback(0..1, message) für echten Fortschritt (Modell laden, Audio laden, Transkribieren).
    Returns: (transkribierter Text, Fehlermeldung oder None).
    """
    if not audio_path or not os.path.isfile(audio_path):
        return ("", "Audiodatei nicht gefunden.")
    try:
        import threading
        import time
        import whisper

        def report(p: float, msg: str) -> None:
            if progress_callback:
                progress_callback(p, msg)

        report(0.0, "Lade Whisper-Modell …")
        model = whisper.load_model(model_size)
        report(0.25, "Lade Audio …")
        audio_array, _ = _load_audio_for_whisper(audio_path)
        report(0.35, "Transkribiere …")

        # Transkription läuft; Fortschritt 35 % → 95 % über geschätzte Dauer (base ~0.5× Echtzeit)
        duration_sec = len(audio_array) / 16000.0
        estimated_sec = max(5, duration_sec * 1.5)
        stop_ev = threading.Event()
        progress_holder: list[float] = [0.35]

        def progress_worker():
            start = time.monotonic()
            while not stop_ev.is_set():
                elapsed = time.monotonic() - start
                p = 0.35 + 0.60 * min(1.0, elapsed / estimated_sec)
                progress_holder[0] = p
                if progress_callback:
                    progress_callback(p, "Transkribiere …")
                stop_ev.wait(0.25)

        t = threading.Thread(target=progress_worker, daemon=True)
        t.start()
        try:
            result = model.transcribe(
                audio_array,
                fp16=torch.cuda.is_available(),
                language=None,
            )
        finally:
            stop_ev.set()
            t.join(timeout=1.0)

        text = (result.get("text") or "").strip()
        report(1.0, "Fertig")
        return (text, None)
    except Exception as e:
        return ("", str(e))
