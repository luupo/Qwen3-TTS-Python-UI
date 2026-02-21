"""
Qwen3-TTS Voice Clone – Windows-UI
Einfaches Tool zum Klonen einer Stimme: Referenz-Audio + Transkript, dann Text eingeben und generieren.
Unterstützt UI-Sprachen: Deutsch (Standard bei deutschem Windows), Englisch.
"""
from __future__ import annotations

import json
import os
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

import ui_lang

# Backend erst nach Start der App importieren (damit Fehler in der UI angezeigt werden)
tts_backend = None

# Sprachen wie von Qwen3-TTS unterstützt (für generierte Sprache)
LANGUAGES = [
    "Auto",
    "Chinese",
    "English",
    "Japanese",
    "Korean",
    "German",
    "French",
    "Russian",
    "Portuguese",
    "Spanish",
    "Italian",
]

MODEL_OPTION_IDS = [
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
]
# Labels werden in _build_ui aus ui_lang geladen (de/en)


def ensure_backend():
    global tts_backend
    if tts_backend is None:
        import tts_backend as _m
        tts_backend = _m
    return tts_backend


class VoiceCloneApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.minsize(780, 1200)
        self.geometry("860x1320")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.model = None
        # UI-Sprache: aus Einstellungen oder Windows (Deutsch bei deutschem Windows)
        self._ui_lang = "de"
        self._load_ui_lang_from_settings()
        self.t = lambda key, **kw: ui_lang.get_text(self._ui_lang, key, **kw)
        self.title(self.t("app_title"))
        self.ref_audio_path = tk.StringVar(value="")
        self.synth_text_var = tk.StringVar(value="")
        self.language_var = ctk.StringVar(value="German")
        self.output_path_var = tk.StringVar(value="")
        self.export_format_var = ctk.StringVar(value="WAV")
        self.model_choice_var = ctk.StringVar(value=MODEL_OPTION_IDS[0])
        self.model_dir_var = tk.StringVar(value="")  # Lokaler Modellordner (Vorrang vor Preset)
        self.download_path_var = tk.StringVar(value="")  # Speicherort für HF-Downloads (leer = Standard-Cache)
        self.use_flash_var = ctk.BooleanVar(value=False)
        self._model_loading = False
        self._load_progress_job = None
        self._load_progress_holder = [0.0, ""]  # [progress 0..1, message] – vom Backend per Callback gesetzt
        self._generation_in_progress = False
        self._gen_progress_job = None
        self._gen_estimated_sec = 15
        self._gen_start_time = None

        self._build_ui()
        self.model_dir_var.trace_add("write", lambda *_: self._update_load_button_text())
        self.export_format_var.trace_add("write", lambda *_: self._sync_output_extension())
        self._set_default_output()
        self._load_settings()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_ui_lang_from_settings(self):
        """Liest UI-Sprache aus Einstellungsdatei (vor _build_ui)."""
        try:
            path = Path(__file__).resolve().parent / "voice_clone_settings.json"
            if path.is_file():
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("ui_language") in ("de", "en"):
                    self._ui_lang = data["ui_language"]
                    return
        except Exception:
            pass
        self._ui_lang = ui_lang.get_default_ui_locale()

    def _build_ui(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Titel
        title = ctk.CTkLabel(main, text=self.t("main_title"), font=ctk.CTkFont(size=22, weight="bold"))
        title.pack(pady=(0, 16))

        # Modell laden
        model_options = [(self.t("preset_06"), MODEL_OPTION_IDS[0]), (self.t("preset_17"), MODEL_OPTION_IDS[1])]
        model_frame = ctk.CTkFrame(main, fg_color=("gray85", "gray25"))
        model_frame.pack(fill="x", pady=(0, 12))
        model_inner = ctk.CTkFrame(model_frame, fg_color="transparent")
        model_inner.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(model_inner, text=self.t("model"), font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        ctk.CTkLabel(model_inner, text=self.t("model_dir_hint")).pack(anchor="w", pady=(4, 2))
        model_dir_row = ctk.CTkFrame(model_inner, fg_color="transparent")
        model_dir_row.pack(fill="x", pady=(0, 4))
        ctk.CTkEntry(model_dir_row, textvariable=self.model_dir_var, width=400).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(model_dir_row, text=self.t("browse_folder"), width=110, command=self._browse_model_dir).pack(side="left")
        ctk.CTkLabel(model_inner, text=self.t("download_path_hint")).pack(anchor="w", pady=(8, 2))
        download_row = ctk.CTkFrame(model_inner, fg_color="transparent")
        download_row.pack(fill="x", pady=(0, 4))
        ctk.CTkEntry(download_row, textvariable=self.download_path_var, width=400).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(download_row, text=self.t("browse_folder"), width=110, command=self._browse_download_dir).pack(side="left")
        mod_row = ctk.CTkFrame(model_inner, fg_color="transparent")
        mod_row.pack(fill="x", pady=4)
        ctk.CTkLabel(mod_row, text=self.t("or_preset")).pack(side="left", padx=(0, 8))
        for label, value in model_options:
            ctk.CTkRadioButton(mod_row, text=label, variable=self.model_choice_var, value=value).pack(side="left", padx=(0, 20))
        opt_row = ctk.CTkFrame(model_inner, fg_color="transparent")
        opt_row.pack(fill="x", pady=4)
        ctk.CTkCheckBox(opt_row, text=self.t("flash_attn"), variable=self.use_flash_var).pack(side="left")
        self.btn_load = ctk.CTkButton(model_inner, text=self.t("load_model"), command=self._on_load_model)
        self.btn_load.pack(pady=(8, 0))
        self._update_load_button_text()
        self.progress_load = ctk.CTkProgressBar(model_inner, width=400)
        self.progress_load.set(0)
        self.label_model_status = ctk.CTkLabel(model_inner, text=self.t("model_status_default"), text_color="gray")
        self.label_model_status.pack(anchor="w", pady=(4, 0))
        self.label_device_status = ctk.CTkLabel(model_inner, text="", text_color="gray")
        self.label_device_status.pack(anchor="w", pady=(2, 0))
        self._update_device_status()

        # Referenz-Audio
        ref_frame = ctk.CTkFrame(main, fg_color=("gray85", "gray25"))
        ref_frame.pack(fill="x", pady=(0, 12))
        ref_inner = ctk.CTkFrame(ref_frame, fg_color="transparent")
        ref_inner.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(ref_inner, text=self.t("ref_audio"), font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        ref_row = ctk.CTkFrame(ref_inner, fg_color="transparent")
        ref_row.pack(fill="x", pady=4)
        ctk.CTkEntry(ref_row, textvariable=self.ref_audio_path, width=400).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(ref_row, text=self.t("file_btn"), width=80, command=self._browse_ref_audio).pack(side="left", padx=(0, 4))
        self.btn_play_ref = ctk.CTkButton(ref_row, text=self.t("play_btn"), width=100, command=self._on_play_ref_audio, fg_color=("gray75", "gray30"))
        self.btn_play_ref.pack(side="left")
        transcript_row = ctk.CTkFrame(ref_inner, fg_color="transparent")
        transcript_row.pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(transcript_row, text=self.t("transcript_label")).pack(side="left", padx=(0, 8))
        self.btn_transcribe = ctk.CTkButton(transcript_row, text=self.t("transcribe_btn"), width=180, command=self._on_transcribe_ref, fg_color=("gray70", "gray35"))
        self.btn_transcribe.pack(side="left")
        self.progress_transcribe = ctk.CTkProgressBar(ref_inner, width=400)
        self.progress_transcribe.set(0)
        self.progress_transcribe.pack(fill="x", pady=(6, 2))
        self.label_transcribe_status = ctk.CTkLabel(ref_inner, text="", text_color="gray")
        self.label_transcribe_status.pack(anchor="w", pady=(0, 4))
        self.ref_text_box = ctk.CTkTextbox(ref_inner, height=180, wrap="word")
        self.ref_text_box.pack(fill="x", pady=(0, 4))
        ref_ph = ui_lang.REF_PLACEHOLDER[0] if self._ui_lang == "de" else ui_lang.REF_PLACEHOLDER[1]
        self.ref_text_box.insert("1.0", ref_ph)

        # Zu sprechender Text
        synth_frame = ctk.CTkFrame(main, fg_color=("gray85", "gray25"))
        synth_frame.pack(fill="x", pady=(0, 12))
        synth_inner = ctk.CTkFrame(synth_frame, fg_color="transparent")
        synth_inner.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(synth_inner, text=self.t("synth_label"), font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.synth_text_box = ctk.CTkTextbox(synth_inner, height=180, wrap="word")
        self.synth_text_box.pack(fill="x", pady=4)
        self.synth_text_box.insert("1.0", ui_lang.SYNTH_PLACEHOLDER_DE if self._ui_lang == "de" else ui_lang.SYNTH_PLACEHOLDER_EN)

        # Sprache & Ausgabe (inkl. UI-Sprache)
        opt_frame = ctk.CTkFrame(main, fg_color=("gray85", "gray25"))
        opt_frame.pack(fill="x", pady=(0, 12))
        opt_inner = ctk.CTkFrame(opt_frame, fg_color="transparent")
        opt_inner.pack(fill="x", padx=12, pady=12)
        self._ui_lang_values = [self.t("ui_lang_de"), self.t("ui_lang_en")]
        row0 = ctk.CTkFrame(opt_inner, fg_color="transparent")
        row0.pack(fill="x", pady=2)
        ctk.CTkLabel(row0, text=self.t("ui_language_label")).pack(side="left", padx=(0, 8))
        self.ui_lang_var = ctk.StringVar(value=self._ui_lang_values[0] if self._ui_lang == "de" else self._ui_lang_values[1])
        self._ui_lang_menu = ctk.CTkOptionMenu(row0, values=self._ui_lang_values, variable=self.ui_lang_var, width=100, command=self._on_ui_lang_change)
        self._ui_lang_menu.pack(side="left", padx=(0, 24))
        row1 = ctk.CTkFrame(opt_inner, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        ctk.CTkLabel(row1, text=self.t("language")).pack(side="left", padx=(0, 8))
        ctk.CTkOptionMenu(row1, values=LANGUAGES, variable=self.language_var, width=120).pack(side="left", padx=(0, 16))
        ctk.CTkLabel(row1, text=self.t("export_format")).pack(side="left", padx=(0, 8))
        ctk.CTkOptionMenu(row1, values=["WAV", "MP3"], variable=self.export_format_var, width=80).pack(side="left", padx=(0, 8))
        self.label_export_hint = ctk.CTkLabel(row1, text="", text_color="gray")
        self.label_export_hint.pack(side="left")
        row2 = ctk.CTkFrame(opt_inner, fg_color="transparent")
        row2.pack(fill="x", pady=6)
        ctk.CTkLabel(row2, text=self.t("output_file")).pack(side="left", padx=(0, 8))
        ctk.CTkEntry(row2, textvariable=self.output_path_var, width=350).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(row2, text=self.t("save_as"), width=110, command=self._browse_output).pack(side="left")

        # Start-Bereich
        start_frame = ctk.CTkFrame(main, fg_color=("gray90", "gray20"), corner_radius=8)
        start_frame.pack(fill="x", pady=(16, 8))
        start_inner = ctk.CTkFrame(start_frame, fg_color="transparent")
        start_inner.pack(fill="x", padx=16, pady=16)
        ctk.CTkLabel(start_inner, text=self.t("start"), font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(start_inner, text=self.t("start_hint"), text_color="gray").pack(anchor="w", pady=(0, 8))
        btn_row = ctk.CTkFrame(start_inner, fg_color="transparent")
        btn_row.pack(fill="x")
        self.btn_generate = ctk.CTkButton(btn_row, text=self.t("btn_generate"), command=self._on_generate, height=44, font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_generate.pack(side="left", padx=(0, 12))
        self.label_start_hint = ctk.CTkLabel(btn_row, text=self.t("load_model_auto"), text_color="gray")
        self.label_start_hint.pack(side="left")
        self.progress_gen = ctk.CTkProgressBar(start_inner, width=400)
        self.progress_gen.set(0)
        self.label_status = ctk.CTkLabel(start_inner, text="", text_color="gray")
        self.label_status.pack(anchor="w", pady=(8, 0))

    def _set_default_output(self):
        out = Path.home() / "Documents" / "QwenTTS_Output"
        out.mkdir(parents=True, exist_ok=True)
        self.output_path_var.set(str(out / "output.wav"))

    def _settings_path(self) -> Path:
        return Path(__file__).resolve().parent / "voice_clone_settings.json"

    def _save_settings(self):
        try:
            data = {
                "model_dir": self.model_dir_var.get().strip(),
                "download_path": self.download_path_var.get().strip(),
                "model_choice": self.model_choice_var.get(),
                "use_flash": self.use_flash_var.get(),
                "ref_audio": self.ref_audio_path.get().strip(),
                "ref_text": self.ref_text_box.get("1.0", "end").strip(),
                "synth_text": self.synth_text_box.get("1.0", "end").strip(),
                "language": self.language_var.get(),
                "export_format": self.export_format_var.get(),
                "output_path": self.output_path_var.get().strip(),
            "ui_language": self._ui_lang,
            }
            path = self._settings_path()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_settings(self):
        try:
            path = self._settings_path()
            if not path.is_file():
                return
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("model_dir"):
                self.model_dir_var.set(data["model_dir"])
            if data.get("download_path"):
                self.download_path_var.set(data["download_path"])
            if data.get("model_choice") in MODEL_OPTION_IDS:
                self.model_choice_var.set(data["model_choice"])
            if "use_flash" in data:
                self.use_flash_var.set(bool(data["use_flash"]))
            if data.get("ref_audio"):
                self.ref_audio_path.set(data["ref_audio"])
            if "ref_text" in data and data["ref_text"]:
                self.ref_text_box.delete("1.0", "end")
                self.ref_text_box.insert("1.0", data["ref_text"])
            if "synth_text" in data and data["synth_text"]:
                self.synth_text_box.delete("1.0", "end")
                self.synth_text_box.insert("1.0", data["synth_text"])
            if data.get("language") in LANGUAGES:
                self.language_var.set(data["language"])
            if data.get("output_path"):
                self.output_path_var.set(data["output_path"])
            if data.get("export_format") in ("WAV", "MP3"):
                self.export_format_var.set(data["export_format"])
            if data.get("ui_language") in ("de", "en"):
                self._ui_lang = data["ui_language"]
        except Exception:
            pass

    def _on_close(self):
        self._save_settings()
        self.destroy()

    def _on_ui_lang_change(self, choice: str):
        """UI-Sprache wechseln (wirksam nach Neustart)."""
        code = "de" if choice == self._ui_lang_values[0] else "en"
        if code == self._ui_lang:
            return
        self._ui_lang = code
        self._save_settings()
        messagebox.showinfo(self.t("app_title"), self.t("restart_for_lang"))

    def _browse_ref_audio(self):
        path = filedialog.askopenfilename(
            title=self.t("dlg_ref_audio"),
            filetypes=[("Audio", "*.wav *.mp3 *.flac *.ogg"), ("Alle", "*.*")],
        )
        if path:
            self.ref_audio_path.set(path)

    def _on_play_ref_audio(self):
        path = self.ref_audio_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showwarning(self.t("dlg_play"), self.t("warn_ref_audio"))
            return
        self.btn_play_ref.configure(state="disabled", text=self.t("playing"))
        def run():
            try:
                import librosa
                import sounddevice as sd
                y, sr = librosa.load(path, sr=None, mono=True)
                sd.play(y, sr)
                sd.wait()
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(self.t("dlg_play"), str(e)))
            self.after(0, lambda: self.btn_play_ref.configure(state="normal", text=self.t("play_btn")))
        threading.Thread(target=run, daemon=True).start()

    def _on_transcribe_ref(self):
        path = self.ref_audio_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showwarning(self.t("dlg_transcript"), self.t("warn_ref_audio"))
            return
        self.btn_transcribe.configure(state="disabled", text=self.t("transcribing"))
        self.progress_transcribe.set(0)
        self.label_transcribe_status.configure(text=self.t("starte"), text_color="gray")
        self.label_status.configure(text="", text_color="gray")

        def progress_callback(progress: float, message: str):
            def update():
                self.progress_transcribe.set(min(1.0, max(0.0, progress)))
                self.label_transcribe_status.configure(text=message, text_color="gray")
            self.after(0, update)

        def run():
            try:
                backend = ensure_backend()
                text, err = backend.transcribe_audio(
                    path, model_size="base", progress_callback=progress_callback
                )
                if err:
                    self.after(0, lambda: self._transcribe_done("", err))
                else:
                    self.after(0, lambda: self._transcribe_done(text, None))
            except Exception as e:
                self.after(0, lambda: self._transcribe_done("", str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _transcribe_done(self, text: str, err: str | None):
        self.btn_transcribe.configure(state="normal", text=self.t("transcribe_btn"))
        self.progress_transcribe.set(1.0 if not err else 0)
        self.label_transcribe_status.configure(text=self.t("transcribe_done") if not err else "")
        self.label_status.configure(text="")
        if err:
            messagebox.showerror(self.t("dlg_transcript"), self.t("error_transcribe", err=err))
            return
        self.ref_text_box.delete("1.0", "end")
        self.ref_text_box.insert("1.0", text or "")

    def _browse_model_dir(self):
        path = filedialog.askdirectory(title=self.t("dlg_model_dir"))
        if path:
            self.model_dir_var.set(path)

    def _browse_download_dir(self):
        path = filedialog.askdirectory(title=self.t("dlg_download_dir"))
        if path:
            self.download_path_var.set(path)

    def _sync_output_extension(self):
        """Passt die Endung in der Ausgabe-Pfad-Box an das gewählte Export-Format an."""
        path = self.output_path_var.get().strip()
        if path:
            fmt = self.export_format_var.get().strip().upper()
            ext = ".mp3" if fmt == "MP3" else ".wav"
            p = Path(path)
            if p.suffix.lower() != ext:
                self.output_path_var.set(str(p.with_suffix(ext)))
        if getattr(self, "label_export_hint", None) is not None:
            fmt = self.export_format_var.get().strip().upper()
            self.label_export_hint.configure(text=self.t("ffmpeg_hint") if fmt == "MP3" else "")

    def _browse_output(self):
        fmt = self.export_format_var.get().strip().lower()
        ext = ".wav" if fmt == "wav" else ".mp3"
        filetypes = [("WAV", "*.wav"), ("MP3", "*.mp3"), ("Alle", "*.*")] if fmt == "wav" else [("MP3", "*.mp3"), ("WAV", "*.wav"), ("Alle", "*.*")]
        path = filedialog.asksaveasfilename(
            title=self.t("dlg_save_as"),
            defaultextension=ext,
            filetypes=filetypes,
        )
        if path:
            self.output_path_var.set(path)

    def _update_device_status(self):
        """Zeigt an, ob CUDA (GPU) genutzt wird – erklärt 0 % GPU bei CPU-only PyTorch."""
        if getattr(self, "label_device_status", None) is None:
            return
        try:
            backend = ensure_backend()
            device, cuda_ok = backend.get_device_info()
            if cuda_ok:
                self.label_device_status.configure(
                    text=self.t("device_cuda", device=device),
                    text_color="green",
                )
            else:
                self.label_device_status.configure(
                    text=self.t("device_cpu"),
                    text_color="gray",
                )
        except Exception:
            self.label_device_status.configure(text="", text_color="gray")

    def _update_load_button_text(self):
        if getattr(self, "btn_load", None) is None or self._model_loading:
            return
        model_dir = self.model_dir_var.get().strip()
        if model_dir and os.path.isdir(model_dir):
            self.btn_load.configure(text=self.t("load_model_local"))
        else:
            self.btn_load.configure(text=self.t("load_model"))

    def _tick_load_progress(self):
        if not self._model_loading:
            return
        p, msg = self._load_progress_holder[0], self._load_progress_holder[1]
        self.progress_load.set(p)
        if msg:
            self.label_model_status.configure(text=msg, text_color="gray")
        self._load_progress_job = self.after(200, self._tick_load_progress)

    def _on_load_model(self):
        self._model_loading = True
        self._load_progress_holder[0] = 0.0
        self._load_progress_holder[1] = self.t("starte")
        model_dir = self.model_dir_var.get().strip()
        is_local = bool(model_dir and os.path.isdir(model_dir))
        self.btn_load.configure(state="disabled", text=self.t("loading"))
        self.label_model_status.configure(
            text=self.t("model_loading_local") if is_local else self.t("model_loading"),
            text_color="gray",
        )
        self.progress_load.set(0)
        self.progress_load.pack(fill="x", pady=(8, 0))
        self._tick_load_progress()
        self.update_idletasks()

        def run():
            try:
                backend = ensure_backend()
                if model_dir and os.path.isdir(model_dir):
                    model_name = os.path.abspath(model_dir)
                else:
                    model_name = self.model_choice_var.get()
                cache_dir = self._get_cache_dir() if not (self.model_dir_var.get().strip() and os.path.isdir(self.model_dir_var.get().strip())) else None
                progress_callback = lambda p, m: (self._load_progress_holder.__setitem__(0, p), self._load_progress_holder.__setitem__(1, m))
                self.model = backend.load_model(
                    model_name=model_name,
                    use_flash_attn=self.use_flash_var.get(),
                    cache_dir=cache_dir,
                    progress_callback=progress_callback,
                )
                self.after(0, self._model_loaded_ok)
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self._model_loaded_fail(err_msg))

        threading.Thread(target=run, daemon=True).start()

    def _model_loaded_ok(self, run_generate_after: bool = False):
        self._model_loading = False
        if self._load_progress_job:
            self.after_cancel(self._load_progress_job)
            self._load_progress_job = None
        self.progress_load.set(1.0)
        self.progress_load.pack_forget()
        self._update_load_button_text()
        self.btn_load.configure(state="normal")
        self.label_model_status.configure(text=self.t("model_loaded"), text_color="green")
        self.label_start_hint.configure(text="")
        if run_generate_after:
            self.after(0, self._do_generate)

    def _model_loaded_fail(self, err: str):
        self._model_loading = False
        if self._load_progress_job:
            self.after_cancel(self._load_progress_job)
            self._load_progress_job = None
        self.progress_load.pack_forget()
        self._update_load_button_text()
        self.btn_load.configure(state="normal")
        self.btn_generate.configure(state="normal", text=self.t("btn_generate"))
        self.label_status.configure(text="")
        self.label_model_status.configure(text=self.t("error_prefix", msg=err[:80] + "…"), text_color="red")
        messagebox.showerror(self.t("dlg_load_model"), self.t("error_load_model", err=err))

    def _get_model_name(self):
        model_dir = self.model_dir_var.get().strip()
        if model_dir and os.path.isdir(model_dir):
            return os.path.abspath(model_dir)
        return self.model_choice_var.get()

    def _get_cache_dir(self):
        """Speicherort für Hugging-Face-Downloads (nur wenn von HF geladen)."""
        path = self.download_path_var.get().strip()
        if not path:
            return None
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except OSError:
            return None

    def _on_generate(self):
        ref_audio = self.ref_audio_path.get().strip()
        ref_text = self.ref_text_box.get("1.0", "end").strip()
        text = self.synth_text_box.get("1.0", "end").strip()
        out = self.output_path_var.get().strip()
        lang = self.language_var.get()

        if not ref_audio or not os.path.isfile(ref_audio):
            messagebox.showwarning(self.t("dlg_input"), self.t("warn_ref_audio"))
            return
        if not ref_text:
            messagebox.showwarning(self.t("dlg_input"), self.t("warn_transcript"))
            return
        if not text:
            messagebox.showwarning(self.t("dlg_input"), self.t("warn_text"))
            return
        if not out:
            messagebox.showwarning(self.t("dlg_input"), self.t("warn_output"))
            return

        # Modell noch nicht geladen → zuerst laden, danach automatisch generieren
        if self.model is None:
            model_dir = self.model_dir_var.get().strip()
            if model_dir and "CustomVoice" in model_dir and "Base" not in model_dir:
                if not messagebox.askyesno(
                    self.t("dlg_model_type"),
                    self.t("confirm_custom_voice"),
                    default=False,
                ):
                    return
            self._start_load_then_generate()
            return
        self._do_generate()

    def _start_load_then_generate(self):
        self.btn_generate.configure(state="disabled", text="⏳ " + self.t("generating_load"))
        self.label_status.configure(text=self.t("generating_then"))
        self._model_loading = True
        self._load_progress_holder[0] = 0.0
        self._load_progress_holder[1] = self.t("starte")
        model_dir = self.model_dir_var.get().strip()
        is_local = bool(model_dir and os.path.isdir(model_dir))
        self.btn_load.configure(state="disabled", text=self.t("loading"))
        self.label_model_status.configure(
            text=self.t("model_loading_local") if is_local else self.t("model_loading"),
            text_color="gray",
        )
        self.progress_load.set(0)
        self.progress_load.pack(fill="x", pady=(8, 0))
        self._tick_load_progress()

        def run():
            try:
                backend = ensure_backend()
                model_name = self._get_model_name()
                cache_dir = self._get_cache_dir() if not (self.model_dir_var.get().strip() and os.path.isdir(self.model_dir_var.get().strip())) else None
                progress_callback = lambda p, m: (self._load_progress_holder.__setitem__(0, p), self._load_progress_holder.__setitem__(1, m))
                self.model = backend.load_model(
                    model_name=model_name,
                    use_flash_attn=self.use_flash_var.get(),
                    cache_dir=cache_dir,
                    progress_callback=progress_callback,
                )
                self.after(0, lambda: self._model_loaded_ok(run_generate_after=True))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self._model_loaded_fail(err_msg))

        threading.Thread(target=run, daemon=True).start()

    def _tick_gen_progress(self):
        if not self._generation_in_progress:
            return
        elapsed = time.time() - self._gen_start_time
        est = max(1, self._gen_estimated_sec)
        p = elapsed / est
        if p >= 0.95:
            # Nach 95 % langsam weiter bis 99 %, damit der Balken nicht starr wirkt
            extra = elapsed - 0.95 * est
            p = 0.95 + 0.04 * min(1.0, extra / 60.0)
        else:
            p = min(0.95, p)
        self.progress_gen.set(p)
        self.label_status.configure(text=self.t("generating_pct", p=int(p * 100)), text_color="gray")
        self._gen_progress_job = self.after(200, self._tick_gen_progress)

    def _do_generate(self):
        ref_audio = self.ref_audio_path.get().strip()
        ref_text = self.ref_text_box.get("1.0", "end").strip()
        text = self.synth_text_box.get("1.0", "end").strip()
        out = self.output_path_var.get().strip()
        lang = self.language_var.get()

        # Geschätzte Dauer aus Textlänge (ca. 30–50 ms pro Zeichen + Basis)
        self._gen_estimated_sec = max(8, 4 + len(text) * 0.04)
        self._gen_start_time = time.time()
        self._generation_in_progress = True
        self.btn_generate.configure(state="disabled", text="⏳ " + self.t("generating"))
        self.progress_gen.set(0)
        self.progress_gen.pack(fill="x", pady=(8, 0))
        self._tick_gen_progress()

        out_fmt = self.export_format_var.get().strip().upper()
        if out_fmt not in ("WAV", "MP3"):
            out_fmt = "WAV"

        def run():
            backend = ensure_backend()
            result_path, err = backend.generate_voice_clone(
                self.model,
                text=text,
                language=lang,
                ref_audio_path=ref_audio,
                ref_text=ref_text,
                output_path=out,
                output_format=out_fmt,
            )
            if err:
                self.after(0, lambda: self._generate_done(False, err))
            else:
                self.after(0, lambda: self._generate_done(True, result_path))

        threading.Thread(target=run, daemon=True).start()

    def _generate_done(self, ok: bool, msg: str):
        self._generation_in_progress = False
        if self._gen_progress_job:
            self.after_cancel(self._gen_progress_job)
            self._gen_progress_job = None
        self.progress_gen.set(1.0)
        self.progress_gen.pack_forget()
        self.btn_generate.configure(state="normal", text=self.t("btn_generate"))
        if ok:
            self.label_status.configure(text=self.t("saved", path=msg), text_color="green")
            messagebox.showinfo(self.t("dlg_done"), self.t("info_saved", path=msg))
        else:
            self.label_status.configure(text=self.t("error_prefix", msg=msg[:60] + "…"), text_color="red")
            messagebox.showerror(self.t("dlg_generation"), self.t("error_generate", msg=msg))


def main():
    app = VoiceCloneApp()
    app.mainloop()


if __name__ == "__main__":
    main()
