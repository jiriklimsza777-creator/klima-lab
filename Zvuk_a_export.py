# -*- coding: utf-8 -*-
import io
import os
import subprocess
import tempfile
import json

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


def _estimate_pitch_autocorr(frame, sample_rate, fmin=60.0, fmax=1200.0):
    """Return estimated fundamental frequency in Hz or None."""
    if frame is None or frame.size < 32:
        return None
    x = frame.astype(np.float32)
    x = x - float(np.mean(x))
    rms = float(np.sqrt(np.mean(x * x) + 1e-10))
    if rms < 0.01:
        return None
    x = x * np.hanning(x.size).astype(np.float32)
    ac = np.correlate(x, x, mode="full")[x.size - 1 :]
    if ac.size < 3:
        return None
    ac[0] = 0.0
    lag_min = int(max(1, sample_rate / float(fmax)))
    lag_max = int(min(ac.size - 1, sample_rate / float(fmin)))
    if lag_max <= lag_min:
        return None
    region = ac[lag_min:lag_max]
    if region.size == 0:
        return None
    best = int(np.argmax(region)) + lag_min
    if best <= 0:
        return None
    freq = float(sample_rate) / float(best)
    if freq < fmin or freq > fmax:
        return None
    return freq


def _extract_motif_notes_from_wav(wav_bytes, bpm, bars=4, quantize_strength=0.75, simplify=0.6):
    """
    Extract producer-friendly monophonic motif notes from wav bytes.
    Returns internal note format [[start_beat, pitch, dur_beat, velocity], ...].
    """
    if not wav_bytes:
        return []
    try:
        sample_rate, audio = _wav_bytes_to_mono_float32(wav_bytes)
    except Exception:
        return []
    if audio.size < 2048:
        return []

    # Lightweight "melody focus": suppress very low-frequency energy.
    k = max(8, int(sample_rate * 0.01))
    smooth = np.convolve(audio, np.ones(k, dtype=np.float32) / float(k), mode="same")
    focused = np.clip(audio - smooth, -1.0, 1.0)

    frame = 2048
    hop = 256
    n_frames = 1 + (len(focused) - frame) // hop
    if n_frames < 8:
        return []

    energy = np.empty(n_frames, dtype=np.float32)
    pitches = np.full(n_frames, -1, dtype=np.int16)
    for i in range(n_frames):
        seg = focused[i * hop : i * hop + frame]
        energy[i] = float(np.sqrt(np.mean(seg * seg) + 1e-10))
        freq = _estimate_pitch_autocorr(seg, sample_rate)
        if freq is not None:
            midi = int(round(69.0 + 12.0 * np.log2(max(1e-6, freq / 440.0))))
            pitches[i] = int(max(24, min(108, midi)))

    thr = float(np.percentile(energy, 60))
    active = (energy >= max(0.008, thr)) & (pitches >= 0)
    if not np.any(active):
        return []

    # Small denoise pass on active mask.
    clean_active = active.copy()
    for i in range(1, n_frames - 1):
        if not active[i] and active[i - 1] and active[i + 1]:
            clean_active[i] = True
        if active[i] and (not active[i - 1]) and (not active[i + 1]):
            clean_active[i] = False
    active = clean_active

    beat_per_sec = float(max(40.0, min(220.0, float(bpm or 90.0)))) / 60.0
    notes = []
    i = 0
    while i < n_frames:
        if not active[i]:
            i += 1
            continue
        j = i + 1
        while j < n_frames and active[j]:
            j += 1
        seg_p = pitches[i:j]
        seg_e = energy[i:j]
        valid_p = seg_p[seg_p >= 0]
        if valid_p.size > 0:
            pitch = int(np.median(valid_p))
            start_sec = (i * hop) / float(sample_rate)
            end_sec = ((j * hop) + frame) / float(sample_rate)
            start_b = start_sec * beat_per_sec
            dur_b = max(0.05, (end_sec - start_sec) * beat_per_sec)
            vel = int(max(35, min(120, 30 + 95 * float(np.mean(seg_e) / (float(np.max(energy)) + 1e-6)))))
            notes.append([start_b, pitch, dur_b, vel])
        i = j

    if not notes:
        return []

    # Quantize and simplify.
    grid = 0.25  # 1/16 note in beats
    qs = float(max(0.0, min(1.0, quantize_strength)))
    min_dur = 0.08 + (1.0 - float(max(0.0, min(1.0, simplify)))) * 0.15

    for n in notes:
        s = float(n[0])
        d = float(n[2])
        qs_s = round(s / grid) * grid
        qe = round((s + d) / grid) * grid
        n[0] = s + (qs_s - s) * qs
        end_m = (s + d) + (qe - (s + d)) * qs
        n[2] = max(min_dur, end_m - n[0])
        n[1] = int(max(24, min(108, n[1])))

    notes.sort(key=lambda x: (float(x[0]), int(x[1])))

    merged = []
    merge_pitch_tol = 1
    for n in notes:
        if n[2] < min_dur:
            continue
        if not merged:
            merged.append(n)
            continue
        prev = merged[-1]
        prev_end = float(prev[0]) + float(prev[2])
        gap = float(n[0]) - prev_end
        if abs(int(n[1]) - int(prev[1])) <= merge_pitch_tol and gap <= 0.15:
            new_end = max(prev_end, float(n[0]) + float(n[2]))
            prev[2] = new_end - float(prev[0])
            prev[3] = int(round((int(prev[3]) + int(n[3])) / 2.0))
        else:
            merged.append(n)

    max_beats = float(max(1, int(bars)) * 4.0)
    out = []
    for n in merged:
        s = float(max(0.0, min(max_beats - 0.05, n[0])))
        d = float(max(0.05, min(max_beats - s, n[2])))
        out.append([round(s, 4), int(n[1]), round(d, 4), int(n[3])])
    return out


def export_smart_boombap_midi_pair(wav_bytes, bpm=90, bars=4, simplify=0.65):
    """
    Returns dict with:
      notes_tight, notes_loose, midi_tight_bytes, midi_loose_bytes
    """
    notes_loose = _extract_motif_notes_from_wav(
        wav_bytes,
        bpm=bpm,
        bars=bars,
        quantize_strength=0.45,
        simplify=simplify,
    )
    notes_tight = _extract_motif_notes_from_wav(
        wav_bytes,
        bpm=bpm,
        bars=bars,
        quantize_strength=0.85,
        simplify=simplify,
    )
    if not notes_loose and not notes_tight:
        return {
            "notes_tight": [],
            "notes_loose": [],
            "midi_tight_bytes": b"",
            "midi_loose_bytes": b"",
        }
    if not notes_tight:
        notes_tight = list(notes_loose)
    if not notes_loose:
        notes_loose = list(notes_tight)
    return {
        "notes_tight": notes_tight,
        "notes_loose": notes_loose,
        "midi_tight_bytes": export_to_midi(notes_tight, bpm=bpm, instrument_id=0),
        "midi_loose_bytes": export_to_midi(notes_loose, bpm=bpm, instrument_id=0),
    }


def _score_note_sequence(notes):
    """Higher is better: stable rhythm, fewer extreme jumps, reasonable density."""
    if not notes:
        return -1e9
    n = len(notes)
    starts = np.array([float(x[0]) for x in notes], dtype=np.float32)
    pitches = np.array([float(x[1]) for x in notes], dtype=np.float32)
    durs = np.array([float(x[2]) for x in notes], dtype=np.float32)
    if n >= 2:
        gaps = np.diff(starts)
        jumps = np.abs(np.diff(pitches))
        rhythm_stability = -float(np.std(gaps))
        jump_penalty = -float(np.mean(np.maximum(0.0, jumps - 7.0)))
    else:
        rhythm_stability = -0.5
        jump_penalty = -0.5
    dur_penalty = -float(np.mean(np.maximum(0.0, 0.08 - durs)) * 10.0)
    density_penalty = -abs(float(n) - 14.0) * 0.06
    return (n * 0.1) + rhythm_stability + jump_penalty + dur_penalty + density_penalty


def _run_basic_pitch_transcription(wav_bytes, bpm=None, bars=None):
    """
    Run Spotify Basic Pitch via dedicated .venv311 Python and return internal note format.
    Returns (notes, midi_bytes) on success, ([], b"") on failure.
    """
    if not wav_bytes:
        return [], b""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    py311 = os.path.join(base_dir, ".venv311", "Scripts", "python.exe")
    if not os.path.exists(py311):
        return [], b""

    with tempfile.TemporaryDirectory() as tmpd:
        in_wav = os.path.join(tmpd, "in.wav")
        out_midi = os.path.join(tmpd, "out.mid")
        with open(in_wav, "wb") as f:
            f.write(wav_bytes)

        script = (
            "import json;"
            "from basic_pitch.inference import predict;"
            f"model_output,midi_data,note_events=predict(r'''{in_wav}''');"
            f"midi_data.write(r'''{out_midi}''')"
        )
        try:
            subprocess.run(
                [py311, "-c", script],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception:
            return [], b""
        if not os.path.exists(out_midi):
            return [], b""
        try:
            with open(out_midi, "rb") as f:
                midi_bytes = f.read()
        except Exception:
            return [], b""

    notes, midi_bpm, _instr = import_midi_bytes(midi_bytes)
    if not notes:
        return [], b""
    notes.sort(key=lambda x: (float(x[0]), int(x[1])))
    return notes, midi_bytes


def _postprocess_basic_pitch_notes(notes, bars=4):
    """Hard cleanup for Basic Pitch output to avoid over-dense MIDI."""
    if not notes:
        return []
    max_beats = float(max(1, int(bars)) * 4.0)
    cleaned = []
    # 1) normalize range/duration and clamp timeline
    for n in notes:
        s = float(max(0.0, min(max_beats - 0.05, float(n[0]))))
        p = int(max(36, min(92, int(n[1]))))
        d = float(max(0.10, min(max_beats - s, float(n[2]))))
        v = int(max(35, min(120, int(n[3]))))
        cleaned.append([s, p, d, v])
    cleaned.sort(key=lambda x: (float(x[0]), int(x[1])))

    # 2) merge immediate re-triggers of same pitch
    merged = []
    for n in cleaned:
        if not merged:
            merged.append(n)
            continue
        prev = merged[-1]
        prev_end = float(prev[0]) + float(prev[2])
        if int(prev[1]) == int(n[1]) and (float(n[0]) - float(prev[0])) <= 0.20:
            new_end = max(prev_end, float(n[0]) + float(n[2]))
            prev[2] = new_end - float(prev[0])
            prev[3] = int(round((int(prev[3]) + int(n[3])) / 2.0))
        else:
            merged.append(n)

    # 3) cluster close onsets and compact each chord
    onset_groups = []
    cur = []
    for n in merged:
        if not cur:
            cur = [n]
            continue
        if abs(float(n[0]) - float(cur[0][0])) <= 0.10:
            cur.append(n)
        else:
            onset_groups.append(cur)
            cur = [n]
    if cur:
        onset_groups.append(cur)

    compact = []
    for grp in onset_groups:
        grp = sorted(grp, key=lambda x: (int(x[1]), -int(x[3])))
        dedup = []
        for n in grp:
            if any(abs(int(n[1]) - int(d[1])) <= 1 for d in dedup):
                continue
            dedup.append(n)
        if not dedup:
            continue

        # Keep at most 3 tones: low + high + strongest middle.
        if len(dedup) > 3:
            low = dedup[0]
            high = dedup[-1]
            middle_candidates = dedup[1:-1]
            middle = sorted(middle_candidates, key=lambda x: int(x[3]), reverse=True)[0] if middle_candidates else None
            pick = [low]
            if middle is not None and middle is not low and middle is not high:
                pick.append(middle)
            if high is not low:
                pick.append(high)
            dedup = sorted(pick, key=lambda x: int(x[1]))

        # Quantize onset and extend very short durations.
        for n in dedup:
            s = round(float(n[0]) / 0.25) * 0.25
            d = max(0.12, round(float(n[2]) / 0.25) * 0.25)
            compact.append([s, int(n[1]), d, int(n[3])])

    compact.sort(key=lambda x: (float(x[0]), int(x[1])))

    # 4) global note budget
    target_notes = int(max(24, min(96, int(bars) * 16)))
    if len(compact) > target_notes:
        scored = []
        for n in compact:
            score = (float(n[2]) * 2.0) + (float(n[3]) / 127.0)
            scored.append((score, n))
        keep = sorted(scored, key=lambda t: t[0], reverse=True)[:target_notes]
        compact = [n for _, n in keep]
        compact.sort(key=lambda x: (float(x[0]), int(x[1])))

    # 5) final clamp
    out = []
    for n in compact:
        s = float(max(0.0, min(max_beats - 0.05, n[0])))
        d = float(max(0.10, min(max_beats - s, n[2])))
        out.append([round(s, 4), int(n[1]), round(d, 4), int(n[3])])
    return out


def _extract_poly_notes_simple(wav_bytes, bpm, bars=4, max_pitches_per_onset=3):
    """
    Polyphonic extractor for simple chord loops.
    Detects onsets and assigns multiple pitch peaks per onset window.
    """
    if not wav_bytes:
        return []
    try:
        sample_rate, audio = _wav_bytes_to_mono_float32(wav_bytes)
    except Exception:
        return []
    if audio.size < 4096:
        return []

    frame = 2048
    hop = 256
    n_frames = 1 + (len(audio) - frame) // hop
    if n_frames < 10:
        return []

    # Onset envelope from spectral flux.
    prev_mag = None
    flux = np.zeros(n_frames, dtype=np.float32)
    win = np.hanning(frame).astype(np.float32)
    for i in range(n_frames):
        seg = audio[i * hop : i * hop + frame] * win
        mag = np.abs(np.fft.rfft(seg)).astype(np.float32)
        if prev_mag is not None:
            diff = mag - prev_mag
            flux[i] = float(np.sum(np.maximum(diff, 0.0)))
        prev_mag = mag

    if float(np.max(flux)) <= 1e-8:
        return []
    flux = flux / float(np.max(flux))

    # Peak pick onsets.
    thr = float(np.percentile(flux, 75))
    onsets = []
    for i in range(2, n_frames - 2):
        if flux[i] >= thr and flux[i] > flux[i - 1] and flux[i] >= flux[i + 1]:
            if not onsets or (i - onsets[-1]) >= int(0.08 * sample_rate / hop):
                onsets.append(i)
    if not onsets:
        onsets = [int(np.argmax(flux))]
    # Merge overly close onsets to avoid chord over-fragmentation.
    merged_onsets = []
    min_gap_frames = int(0.11 * sample_rate / hop)
    for o in onsets:
        if not merged_onsets or (o - merged_onsets[-1]) >= min_gap_frames:
            merged_onsets.append(o)
    onsets = merged_onsets

    beat_per_sec = float(max(40.0, min(220.0, float(bpm or 90.0)))) / 60.0
    min_midi = 36
    max_midi = 96
    notes = []

    for oi, on in enumerate(onsets):
        nxt = onsets[oi + 1] if oi + 1 < len(onsets) else min(n_frames - 1, on + int(0.7 * sample_rate / hop))
        if nxt <= on:
            continue
        start = on * hop
        end = min(len(audio), nxt * hop + frame)
        seg = audio[start:end]
        if seg.size < 512:
            continue

        # Analyze start of note for pitch peaks.
        ana_len = min(seg.size, int(0.35 * sample_rate))
        ana = seg[:ana_len].astype(np.float32)
        ana = ana * np.hanning(ana.size).astype(np.float32)
        mag = np.abs(np.fft.rfft(ana)).astype(np.float32)
        if mag.size < 16:
            continue
        freqs = np.fft.rfftfreq(ana.size, 1.0 / float(sample_rate))
        fmin = 55.0
        fmax = 1800.0
        idx = np.where((freqs >= fmin) & (freqs <= fmax))[0]
        if idx.size == 0:
            continue
        sub_mag = mag[idx]
        sub_freq = freqs[idx]
        if float(np.max(sub_mag)) <= 1e-9:
            continue

        # Pick several local peaks.
        peak_idxs = []
        for k in range(2, len(sub_mag) - 2):
            v = sub_mag[k]
            if v > sub_mag[k - 1] and v >= sub_mag[k + 1] and v > (0.20 * float(np.max(sub_mag))):
                peak_idxs.append(k)
        peak_idxs = sorted(peak_idxs, key=lambda k: float(sub_mag[k]), reverse=True)

        chosen_midi = []
        for k in peak_idxs:
            f = float(sub_freq[k])
            midi = int(round(69.0 + 12.0 * np.log2(max(1e-6, f / 440.0))))
            if midi < min_midi or midi > max_midi:
                continue
            # Remove near-duplicates and common overtone clutter.
            if any(abs(midi - m) <= 1 for m in chosen_midi):
                continue
            if any(abs((midi - m) % 12) in (0, 7) and abs(midi - m) >= 12 for m in chosen_midi):
                continue
            chosen_midi.append(midi)
            if len(chosen_midi) >= int(max_pitches_per_onset):
                break
        if not chosen_midi:
            continue

        start_sec = float(start) / float(sample_rate)
        end_sec = float(end) / float(sample_rate)
        start_b = start_sec * beat_per_sec
        dur_b = max(0.10, (end_sec - start_sec) * beat_per_sec)
        vel_base = int(max(45, min(115, 35 + 90 * float(np.mean(np.abs(ana)) / (float(np.max(np.abs(audio))) + 1e-6)))))

        # Quantize onset lightly, keep duration musical.
        grid = 0.25
        qstart = round(start_b / grid) * grid
        start_b = start_b + (qstart - start_b) * 0.65
        qend = round((start_b + dur_b) / grid) * grid
        dur_b = max(0.10, qend - start_b)

        chord = sorted(chosen_midi)
        # Keep chord compact: max spread 16 semitones (simple lofi voicings).
        while len(chord) > 1 and (max(chord) - min(chord)) > 16:
            chord.pop(-1)
        for j, midi in enumerate(chord):
            vel = int(max(35, min(120, vel_base - j * 6)))
            notes.append([round(start_b, 4), int(midi), round(dur_b, 4), vel])

    if not notes:
        return []

    max_beats = float(max(1, int(bars)) * 4.0)
    out = []
    for n in notes:
        s = float(max(0.0, min(max_beats - 0.05, n[0])))
        d = float(max(0.05, min(max_beats - s, n[2])))
        out.append([round(s, 4), int(n[1]), round(d, 4), int(n[3])])
    out.sort(key=lambda x: (float(x[0]), int(x[1])))

    # Final dedupe at same onset: keep strongest up to max_pitches_per_onset.
    by_onset = {}
    for n in out:
        key = round(float(n[0]), 3)
        by_onset.setdefault(key, []).append(n)
    pruned = []
    for key in sorted(by_onset.keys()):
        grp = by_onset[key]
        uniq = []
        for n in sorted(grp, key=lambda x: int(x[3]), reverse=True):
            if any(abs(int(n[1]) - int(u[1])) <= 1 for u in uniq):
                continue
            uniq.append(n)
            if len(uniq) >= int(max_pitches_per_onset):
                break
        pruned.extend(sorted(uniq, key=lambda x: int(x[1])))
    return pruned


def export_max_fidelity_midi(wav_bytes, bpm=90, bars=4):
    """
    Single-result extractor tuned for simple loops/chords:
    returns {"notes": [...], "midi_bytes": b"..."}
    """
    # RAW BASIC PITCH mode: no postprocess, no fallback.
    bp_notes, bp_midi_raw = _run_basic_pitch_transcription(wav_bytes, bpm=None, bars=None)
    if bp_notes and bp_midi_raw:
        return {
            "notes": bp_notes,
            "midi_bytes": bp_midi_raw,
        }
    return {"notes": [], "midi_bytes": b""}
