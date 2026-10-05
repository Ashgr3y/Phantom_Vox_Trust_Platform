from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = PROJECT_ROOT / "models" / "rawnetlite"
MODEL_FILE = MODEL_DIR / "RawNetLite.py"
CHECKPOINT_FILE = MODEL_DIR / "augmented_triple_cross_domain_focal_rawnet_lite.pt"


@dataclass
class InferenceWindow:
    start_seconds: float
    end_seconds: float
    synthetic_score: float
    label: str


class RawNetLiteAdapter:
    name = "RawNetLite"
    version = "rawnetlite-checkpoint-1.0"
    purpose = "Lightweight synthetic-speech evidence"
    input_format = "Mono PCM waveform, 16 kHz, 3-second windows"
    limitations = (
        "Uncalibrated checkpoint score. It is evidence for TrustFusion, not a verified probability. "
        "Language, codec, replay, and unseen-generator performance require a labeled benchmark."
    )

    def __init__(self) -> None:
        self._model = None
        self._device = "not loaded"
        self._load_error: str | None = None

    def status(self) -> dict:
        dependencies: list[str] = []
        for module in ("torch", "numpy", "soundfile"):
            if importlib.util.find_spec(module) is None:
                dependencies.append(module)
        installed = MODEL_FILE.exists() and CHECKPOINT_FILE.exists() and not dependencies
        status = "READY" if installed else "OPTIONAL_DEPENDENCIES_MISSING"
        if self._load_error:
            status = "LOAD_FAILED"
        if not MODEL_FILE.exists() or not CHECKPOINT_FILE.exists():
            status = "MODEL_ASSET_MISSING"
        return {
            "name": self.name,
            "purpose": self.purpose,
            "version": self.version,
            "input_format": self.input_format,
            "device": self._device,
            "status": status,
            "installed": installed,
            "active": self._model is not None,
            "missing_dependencies": dependencies,
            "limitations": self.limitations,
            "load_error": self._load_error,
        }

    def _load(self) -> None:
        if self._model is not None:
            return
        status = self.status()
        if not status["installed"]:
            raise RuntimeError(
                "RawNetLite cannot run because optional ML dependencies or model assets are missing: "
                + ", ".join(status.get("missing_dependencies", []))
            )
        try:
            import torch

            if str(MODEL_DIR) not in sys.path:
                sys.path.insert(0, str(MODEL_DIR))
            from RawNetLite import RawNetLite

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = RawNetLite().to(device)
            checkpoint = torch.load(CHECKPOINT_FILE, map_location=device, weights_only=True)
            model.load_state_dict(checkpoint)
            model.eval()
            self._model = model
            self._device = str(device)
            self._load_error = None
        except Exception as exc:
            self._load_error = str(exc)
            raise

    def warmup(self) -> None:
        """Verify checkpoint compatibility and a real forward pass before serving."""
        self._load()
        import torch

        with torch.inference_mode():
            score = self._model(torch.zeros(1, 1, 48000, device=self._device))
        if score.numel() != 1 or not torch.isfinite(score).all() or not 0 <= score.item() <= 1:
            raise RuntimeError("RawNetLite startup inference returned an invalid score")

    def analyze(self, audio_path: str) -> dict:
        self._load()
        import numpy as np
        import soundfile as sf
        import torch

        audio, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        if not len(audio):
            raise ValueError("Audio file is empty")
        if sample_rate != 16000:
            target_length = max(1, int(len(audio) * 16000 / sample_rate))
            audio = np.interp(
                np.linspace(0, len(audio) - 1, target_length),
                np.arange(len(audio)),
                audio,
            ).astype(np.float32)

        window_samples = 48000
        hop = 16000
        duration = len(audio) / 16000
        if len(audio) < window_samples:
            repeats = int(np.ceil(window_samples / len(audio)))
            audio = np.tile(audio, repeats)[:window_samples]
        starts = list(range(0, max(1, len(audio) - window_samples + 1), hop)) or [0]
        if len(audio) > window_samples and starts[-1] != len(audio) - window_samples:
            starts.append(len(audio) - window_samples)

        windows: list[InferenceWindow] = []
        with torch.no_grad():
            for start in starts:
                samples = audio[start : start + window_samples]
                if len(samples) < window_samples:
                    samples = np.pad(samples, (0, window_samples - len(samples)))
                waveform = torch.from_numpy(samples.copy()).float().unsqueeze(0).unsqueeze(0).to(self._device)
                score = float(self._model(waveform).squeeze().item())
                score = max(0.0, min(1.0, score))
                windows.append(
                    InferenceWindow(
                        start_seconds=round(start / 16000, 2),
                        end_seconds=round(min(duration, (start + window_samples) / 16000), 2),
                        synthetic_score=round(score, 4),
                        label="SUSPICIOUS" if score >= 0.5 else "LOW_EVIDENCE",
                    )
                )
        scores = [window.synthetic_score for window in windows]
        return {
            "model": self.name,
            "model_version": self.version,
            "score_type": "UNCALIBRATED_EVIDENCE",
            "duration_seconds": round(duration, 2),
            "synthetic_score": round(sum(scores) / len(scores), 4),
            "peak_synthetic_score": round(max(scores), 4),
            "windows": [asdict(window) for window in windows],
            "raw_audio_retained": False,
        }


rawnetlite_adapter = RawNetLiteAdapter()
