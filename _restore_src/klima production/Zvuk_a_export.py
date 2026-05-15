# -*- coding: utf-8 -*-
import io
import os
import subprocess
import tempfile

import numpy as np
import pretty_midi
from scipy.io import wavfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(BASE_DIR, "fluidsynth", "bin", "fluidsynth.exe")
SF2_PATH = os.path.join(BASE_DIR, "assets", "instrumenty.sf2")


def apply_fade(audio, sample_rate, fade_in=0.01, fade_out=0.05):
    n_in = int(fade_in * sample_rate)
    n_out = int(fade_out * sample_rate)
    if len(audio) > n_in + n_out:
        audio[:n_in] *= np.linspace(0, 1, n_in)
        audio[-n_out:] *= np.linspace(1, 0, n_out)
    return audio


def get_lab_sound(freq, t_dur, sample_rate, instr_id, velocity):
    t = np.linspace(0, t_dur, int(t_dur * sample_rate), False)
    volume = (velocity / 127.0) * 0.5

    if instr_id == 0:
        tone = np.sin(2 * np.pi * freq * t)
    elif instr_id == 1:
        tone = np.sign(np.sin(2 * np.pi * freq * t))
    elif instr_id == 2:
        tone = 2 * (t * freq - np.floor(0.5 + t * freq))
    elif instr_id == 3:
        tone = 2 * np.abs(2 * (t * freq - np.floor(0.5 + t * freq))) - 1
    else:
        tone = np.sin(2 * np.pi * freq * t)

    env = np.exp(-4 * t)
    return apply_fade(tone * env * volume, sample_rate)


def synthesise_full_audio(melody, engine_type="Studio", instrument_id=0, octave_shift=0, bpm=120):
    """Převede notová data na WAV audio."""
    if not melody:
        return b""

    processed_melody = []
    for note in melody:
        if len(note) < 3:
            continue
        processed = list(note)
        processed[1] = int(note[1]) + (octave_shift * 12)
        processed[1] = max(0, min(127, processed[1]))
        processed_melody.append(processed)

    if not processed_melody:
        return b""

    if engine_type == "Laboratoř":
        sample_rate = 22050
        times = [n[0] + n[2] for n in processed_melody]
        total_dur = max(times) * (60.0 / bpm)
        audio = np.zeros(int(total_dur * sample_rate) + 4000)

        for note in processed_melody:
            start, pitch, duration = note[0], note[1], note[2]
            velocity = note[3] if len(note) > 3 else 100
            freq = 440.0 * (2.0 ** ((pitch - 69.0) / 12.0))
            tone = get_lab_sound(freq, duration * (60.0 / bpm), sample_rate, int(instrument_id), velocity)
            idx = int(start * (60.0 / bpm) * sample_rate)
            if idx + len(tone) < len(audio):
                audio[idx : idx + len(tone)] += tone

        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = (audio / max_val * 0.9 * 32767).astype(np.int16)
        else:
            audio = audio.astype(np.int16)

        buffer = io.BytesIO()
        wavfile.write(buffer, sample_rate, audio)
        return buffer.getvalue()

    if not os.path.exists(EXE_PATH) or not os.path.exists(SF2_PATH):
        print(f"Chyba: Soubory pro Studio nebyly nalezeny ({EXE_PATH})")
        return b""

    midi_tmp = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
    wav_tmp_path = midi_tmp.name.replace(".mid", ".wav")

    try:
        midi_binary = export_to_midi(processed_melody, bpm, instrument_id)
        midi_tmp.write(midi_binary)
        midi_tmp.close()

        cmd = [EXE_PATH, "-ni", SF2_PATH, midi_tmp.name, "-F", wav_tmp_path, "-r", "44100"]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if os.path.exists(wav_tmp_path):
            with open(wav_tmp_path, "rb") as f:
                return f.read()
        return b""
    except subprocess.CalledProcessError as e:
        print(f"Chyba Zvuk_a_export: {e}")
        return b""
    finally:
        if os.path.exists(midi_tmp.name):
            os.remove(midi_tmp.name)
        if os.path.exists(wav_tmp_path):
            os.remove(wav_tmp_path)


def export_to_midi(melody, bpm, instrument_id=0):
    """Generuje MIDI soubor z dat v paměti."""
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    instrument = pretty_midi.Instrument(program=int(instrument_id))

    for note in melody:
        try:
            start, pitch, duration = note[0], note[1], note[2]
            velocity = note[3] if len(note) > 3 else 100
            midi_note = pretty_midi.Note(
                velocity=int(max(1, min(127, velocity))),
                pitch=int(max(0, min(127, pitch))),
                start=float(start * (60.0 / bpm)),
                end=float((start + duration) * (60.0 / bpm)),
            )
            instrument.notes.append(midi_note)
        except Exception:
            continue

    pm.instruments.append(instrument)
    midi_data = io.BytesIO()
    pm.write(midi_data)
    return midi_data.getvalue()


def import_midi_bytes(midi_bytes):
    """
    Parse MIDI bytes into internal melody format:
    [[start_beats, pitch, duration_beats, velocity], ...], bpm, instrument_name
    """
    if not midi_bytes:
        return [], 90, "Acoustic Grand Piano"
    try:
        pm = pretty_midi.PrettyMIDI(io.BytesIO(midi_bytes))
    except Exception:
        return [], 90, "Acoustic Grand Piano"

    bpm = 90
    try:
        changes = pm.get_tempo_changes()
        if len(changes) >= 2 and len(changes[1]) > 0:
            bpm = int(round(float(changes[1][0])))
    except Exception:
        bpm = 90
    bpm = max(40, min(220, int(bpm or 90)))

    instrument = None
    for ins in pm.instruments:
        if ins.notes:
            instrument = ins
            break
    if instrument is None:
        return [], bpm, "Acoustic Grand Piano"

    name = instrument.name.strip() if getattr(instrument, "name", None) else "Acoustic Grand Piano"
    if not name:
        name = "Acoustic Grand Piano"

    melody = []
    beat_sec = 60.0 / float(bpm)
    for n in instrument.notes:
        try:
            start_b = round(float(n.start) / beat_sec, 4)
            dur_b = round(max(0.01, (float(n.end) - float(n.start)) / beat_sec), 4)
            melody.append([start_b, int(n.pitch), dur_b, int(max(1, min(127, n.velocity)))])
        except Exception:
            continue
    melody.sort(key=lambda x: (float(x[0]), int(x[1])))
    return melody, bpm, name


def mix_wav_audios(audio_blobs):
    """Smíchá více WAV blobů do jednoho WAV blobu."""
    valid = [blob for blob in audio_blobs if blob]
    if not valid:
        return b""

    tracks = []
    sample_rate = None
    max_len = 0

    for blob in valid:
        buf = io.BytesIO(blob)
        rate, data = wavfile.read(buf)
        if data.ndim > 1:
            data = data.mean(axis=1)
        data = data.astype(np.float32)

        if sample_rate is None:
            sample_rate = rate
        if rate != sample_rate:
            continue

        tracks.append(data)
        max_len = max(max_len, len(data))

    if not tracks or sample_rate is None:
        return b""

    mix = np.zeros(max_len, dtype=np.float32)
    for track in tracks:
        mix[: len(track)] += track

    max_val = np.max(np.abs(mix))
    if max_val > 0:
        mix = (mix / max_val) * 32767 * 0.9

    output = io.BytesIO()
    wavfile.write(output, sample_rate, mix.astype(np.int16))
    return output.getvalue()


def estimate_bpm_from_wav_bytes(wav_bytes, bpm_min=60, bpm_max=180):
    """
    Very lightweight tempo estimation from a WAV blob.
    Intended for beat sketches, not for scientific accuracy.
    """
    if not wav_bytes:
        return None

    try:
        rate, data = wavfile.read(io.BytesIO(wav_bytes))
    except Exception:
        return None

    if rate is None or data is None:
        return None

    if data.ndim > 1:
        data = data.mean(axis=1)

    # Convert to float32 in [-1, 1]
    if data.dtype == np.int16:
        audio = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        audio = data.astype(np.float32) / 2147483648.0
    elif data.dtype == np.uint8:
        audio = (data.astype(np.float32) - 128.0) / 128.0
    else:
        audio = data.astype(np.float32)
        max_abs = np.max(np.abs(audio)) if audio.size else 0
        if max_abs > 1.0:
            audio = audio / max_abs

    if audio.size < rate:  # <1s
        return None

    audio = audio - float(np.mean(audio))
    audio = np.clip(audio, -1.0, 1.0)

    # Short-time RMS envelope
    frame = 1024
    hop = 512
    n_frames = 1 + (len(audio) - frame) // hop
    if n_frames <= 10:
        return None

    rms = np.empty(n_frames, dtype=np.float32)
    for i in range(n_frames):
        seg = audio[i * hop : i * hop + frame]
        rms[i] = np.sqrt(np.mean(seg * seg) + 1e-8)

    onset = np.diff(rms, prepend=rms[0])
    onset = np.maximum(onset, 0.0)
    onset = onset - float(np.mean(onset))
    onset = np.maximum(onset, 0.0)

    if float(np.max(onset)) <= 1e-6:
        return None
    onset = onset / float(np.max(onset))

    env_sr = rate / hop
    lag_min = int(env_sr * 60.0 / float(bpm_max))
    lag_max = int(env_sr * 60.0 / float(bpm_min))
    lag_min = max(1, lag_min)
    lag_max = min(len(onset) - 2, lag_max)
    if lag_max <= lag_min:
        return None

    # Autocorrelation via FFT
    n = int(2 ** np.ceil(np.log2(len(onset) * 2)))
    fft = np.fft.rfft(onset, n=n)
    ac = np.fft.irfft(fft * np.conj(fft))[: len(onset)]
    ac[0] = 0.0

    window = ac[lag_min:lag_max]
    if window.size == 0:
        return None
    best = int(np.argmax(window)) + lag_min
    if best <= 0:
        return None

    bpm = 60.0 * env_sr / float(best)
    # Fold into range
    while bpm < bpm_min:
        bpm *= 2.0
    while bpm > bpm_max:
        bpm /= 2.0

    return float(bpm)


def get_wav_duration_seconds(wav_bytes):
    try:
        rate, data = wavfile.read(io.BytesIO(wav_bytes))
    except Exception:
        return None
    if rate is None or data is None:
        return None
    n = data.shape[0]
    if rate <= 0:
        return None
    return float(n) / float(rate)


def _wav_bytes_to_mono_float32(wav_bytes):
    rate, data = wavfile.read(io.BytesIO(wav_bytes))
    if data.ndim > 1:
        data = data.mean(axis=1)
    if data.dtype == np.int16:
        audio = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        audio = data.astype(np.float32) / 2147483648.0
    elif data.dtype == np.uint8:
        audio = (data.astype(np.float32) - 128.0) / 128.0
    else:
        audio = data.astype(np.float32)
        max_abs = float(np.max(np.abs(audio))) if audio.size else 0.0
        if max_abs > 1.0:
            audio = audio / max_abs
    audio = np.clip(audio, -1.0, 1.0)
    return rate, audio


def _mono_float32_to_wav_bytes(sample_rate, audio_float32):
    audio_float32 = np.clip(audio_float32, -1.0, 1.0)
    audio_int16 = (audio_float32 * 32767.0 * 0.95).astype(np.int16)
    out = io.BytesIO()
    wavfile.write(out, int(sample_rate), audio_int16)
    return out.getvalue()


def resample_wav_bytes(wav_bytes, target_sample_rate):
    """Resample WAV blob to target sample rate (mono)."""
    if not wav_bytes:
        return b""
    try:
        src_rate, audio = _wav_bytes_to_mono_float32(wav_bytes)
    except Exception:
        return b""

    target_sample_rate = int(target_sample_rate)
    if src_rate == target_sample_rate:
        return _mono_float32_to_wav_bytes(src_rate, audio)

    if src_rate <= 0 or target_sample_rate <= 0:
        return b""

    src_len = audio.shape[0]
    if src_len < 2:
        return b""

    duration = float(src_len) / float(src_rate)
    tgt_len = int(max(2, round(duration * target_sample_rate)))
    x_old = np.linspace(0.0, duration, num=src_len, endpoint=False, dtype=np.float32)
    x_new = np.linspace(0.0, duration, num=tgt_len, endpoint=False, dtype=np.float32)
    resampled = np.interp(x_new, x_old, audio).astype(np.float32)
    return _mono_float32_to_wav_bytes(target_sample_rate, resampled)


def apply_gain_wav_bytes(wav_bytes, gain=0.7):
    """Apply gain to a WAV blob (mono)."""
    if not wav_bytes:
        return b""
    try:
        rate, audio = _wav_bytes_to_mono_float32(wav_bytes)
    except Exception:
        return b""
    gain = float(gain)
    audio = np.clip(audio * gain, -1.0, 1.0)
    return _mono_float32_to_wav_bytes(rate, audio)
