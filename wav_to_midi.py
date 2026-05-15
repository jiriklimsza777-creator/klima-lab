# -*- coding: utf-8 -*-
import argparse
import os
import sys
from pathlib import Path


def check_dependencies():
    try:
        import basic_pitch
        import mido
    except ImportError as e:
        print(f"Chybí závislost: {e}")
        print("Spusť: pip install basic-pitch mido")
        sys.exit(1)


def convert_wav_to_midi(wav_path, output_dir, min_note_duration=0.08, min_velocity=40):
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    import mido

    wav_path = Path(wav_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / (wav_path.stem + ".mid")

    try:
        model_output, midi_data, note_events = predict(
            str(wav_path),
            minimum_note_length=min_note_duration,
            minimum_frequency=40,
            maximum_frequency=2000,
        )

        filtered_notes = [n for n in note_events if n[3] >= min_velocity]

        if len(filtered_notes) < 1:
            print(f"  PRESKOCENO: {wav_path.name}")
            return False

        mid = mido.MidiFile(ticks_per_beat=96)
        track = mido.MidiTrack()
        track.name = wav_path.stem
        mid.tracks.append(track)

        filtered_notes.sort(key=lambda n: n[0])

        events = []
        for start_sec, end_sec, pitch, amplitude, _ in filtered_notes:
            velocity = min(127, max(1, int(amplitude * 127)))
            start_tick = int(start_sec * 96 * 2)
            end_tick = int(end_sec * 96 * 2)
            duration = max(1, end_tick - start_tick)
            events.append((start_tick, 'on', pitch, velocity))
            events.append((start_tick + duration, 'off', pitch, 0))

        events.sort(key=lambda e: (e[0], 0 if e[1] == 'off' else 1))

        current_tick = 0
        for tick, kind, pitch, vel in events:
            delta = tick - current_tick
            current_tick = tick
            if kind == 'on':
                track.append(mido.Message('note_on', note=pitch, velocity=vel, time=delta))
            else:
                track.append(mido.Message('note_on', note=pitch, velocity=0, time=delta))

        mid.save(str(out_path))
        print(f"  OK ({len(filtered_notes)} not): {out_path.name}")
        return True

    except Exception as e:
        print(f"  CHYBA {wav_path.name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min_note", type=float, default=0.08)
    parser.add_argument("--min_vel", type=int, default=40)
    args = parser.parse_args()

    check_dependencies()

    input_dir = Path(args.input)
    wav_files = list(input_dir.rglob("*.wav")) + list(input_dir.rglob("*.WAV"))

    if not wav_files:
        print("Žádné WAV soubory nenalezeny.")
        sys.exit(1)

    print(f"Nalezeno {len(wav_files)} WAV souborů")
    ok, skipped = 0, 0
    for i, wav in enumerate(wav_files, 1):
        print(f"[{i}/{len(wav_files)}] {wav.name}")
        result = convert_wav_to_midi(wav, args.output, args.min_note, args.min_vel)
        if result:
            ok += 1
        else:
            skipped += 1

    print(f"Hotovo: {ok} převedeno, {skipped} přeskočeno")


if __name__ == "__main__":
    main()