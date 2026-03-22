import whisper
import sys
import os


def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def generate_srt(audio_path, model_size="small", prompt=None):
    if not os.path.exists(audio_path):
        print(f"❌ Error: The file '{audio_path}' was not found.")
        return

    print(f"Loading Whisper model ({model_size})...")
    model = whisper.load_model(model_size)

    print(f"Transcribing: {audio_path}")

    # We add the initial_prompt here to give the AI context
    result = model.transcribe(
        audio_path,
        initial_prompt=prompt,
        fp16=False,  # Set to False if you are running on a CPU without a GPU
    )

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
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        audio_file = "final/final.mp3"

    # CUSTOMIZE YOUR PROMPT HERE:
    # This helps the AI recognize the "Habit X" pattern immediately.
    my_prompt = "Habit 1. Practice Mindfulness. Habit 2. Stay Hydrated."

    generate_srt(audio_file, model_size="small", prompt=my_prompt)
