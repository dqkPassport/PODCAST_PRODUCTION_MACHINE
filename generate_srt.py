# python generate_srt.py final/final85.mp3

import whisper
import sys
import os


def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def generate_srt(audio_path, model_size="base"):
    print("Loading Whisper model...")
    model = whisper.load_model(model_size)

    print("Transcribing audio...")
    result = model.transcribe(audio_path)

    segments = result["segments"]

    srt_path = os.path.splitext(audio_path)[0] + ".srt"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_time(seg["start"])
            end = format_time(seg["end"])
            text = seg["text"].strip()

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")

    print(f"✅ SRT saved to: {srt_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_srt.py audio.mp3")
    else:
        audio_file = sys.argv[1]
        generate_srt(audio_file)
