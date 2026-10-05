"""Optional Windows WASAPI loopback adapter for Phantom Vox.

Audio chunks are kept in memory and are not written to disk unless the user
explicitly sets PHANTOM_VOX_SAVE_LOOPBACK_CHUNKS=true.
"""

from __future__ import annotations

import io
import os
import wave
from datetime import datetime
from pathlib import Path

import pyaudiowpatch as pyaudio
import requests


API_URL = os.getenv("PHANTOM_VOX_AUDIO_ENDPOINT", "http://127.0.0.1:8000/api/v1/sessions/SESSION_ID/audio")
TOKEN = os.getenv("PHANTOM_VOX_TOKEN", "")
CHUNK_SECONDS = float(os.getenv("PHANTOM_VOX_CHUNK_SECONDS", "3"))
SAVE_CHUNKS = os.getenv("PHANTOM_VOX_SAVE_LOOPBACK_CHUNKS", "false").lower() == "true"
CHUNKS_DIR = Path(os.getenv("PHANTOM_VOX_CHUNKS_DIR", "captured_chunks"))
FORMAT = pyaudio.paInt16
FRAMES_PER_BUFFER = 1024


def get_default_loopback_device(audio: pyaudio.PyAudio) -> dict:
    wasapi = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
    speakers = audio.get_device_info_by_index(wasapi["defaultOutputDevice"])
    if speakers["isLoopbackDevice"]:
        return speakers
    for candidate in audio.get_loopback_device_info_generator():
        if speakers["name"] in candidate["name"]:
            return candidate
    raise RuntimeError("No WASAPI loopback device matches the current Windows playback device")


def record_chunk(audio: pyaudio.PyAudio, device: dict) -> io.BytesIO:
    channels = device["maxInputChannels"]
    rate = int(device["defaultSampleRate"])
    stream = audio.open(
        format=FORMAT,
        channels=channels,
        rate=rate,
        input=True,
        input_device_index=device["index"],
        frames_per_buffer=FRAMES_PER_BUFFER,
    )
    try:
        frames = [stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False) for _ in range(int(rate / FRAMES_PER_BUFFER * CHUNK_SECONDS))]
    finally:
        stream.stop_stream()
        stream.close()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(audio.get_sample_size(FORMAT))
        output.setframerate(rate)
        output.writeframes(b"".join(frames))
    buffer.seek(0)
    return buffer


def main() -> None:
    if "SESSION_ID" in API_URL:
        raise SystemExit("Set PHANTOM_VOX_AUDIO_ENDPOINT to a real session audio endpoint")
    if not TOKEN:
        raise SystemExit("Set PHANTOM_VOX_TOKEN to a valid development access token")
    audio = pyaudio.PyAudio()
    try:
        device = get_default_loopback_device(audio)
        print(f"Capturing ephemeral {CHUNK_SECONDS:g}-second windows from {device['name']}")
        if SAVE_CHUNKS:
            CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
            print(f"Explicit retention enabled: {CHUNKS_DIR.resolve()}")
        while True:
            buffer = record_chunk(audio, device)
            if SAVE_CHUNKS:
                path = CHUNKS_DIR / f"chunk_{datetime.now():%Y%m%d_%H%M%S}.wav"
                path.write_bytes(buffer.getvalue())
                buffer.seek(0)
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {TOKEN}"},
                files={"file": ("loopback.wav", buffer, "audio/wav")},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            print(f"synthetic evidence={result['synthetic_score']:.3f} ({result['score_type']})")
    except KeyboardInterrupt:
        print("Stopped")
    finally:
        audio.terminate()


if __name__ == "__main__":
    main()
