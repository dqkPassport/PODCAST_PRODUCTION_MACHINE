# Add random delay between 500ms and 1000ms (0.5s - 1.0s)
# We don't need a delay for the very first file (index 0)
# python combine_longer.py
# It will combine all mp3 files in 'inworld' into 'final/final.mp3' with natural pauses between segments.
import os
import random
import ffmpeg
from pathlib import Path

# --- CONFIGURATION ---
# Your specific Windows path for FFmpeg
FFMPEG_PATH = r"C:\DQK\ffmpeg\bin\ffmpeg.exe"
INPUT_DIR = Path("inworld")
OUTPUT_DIR = Path("final")
OUTPUT_FILE = OUTPUT_DIR / "final.mp3"


def combine_with_random_pauses():
    # 1. Ensure the 'final' output folder exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Get all mp3 files from 'inworld' and sort them
    mp3_files = sorted(
        [f for f in INPUT_DIR.glob("*.mp3") if f.name != "final.mp3"],
        key=lambda x: x.name,
    )

    if not mp3_files:
        print(f"❌ No .mp3 files found in {INPUT_DIR}")
        return

    print(f"📚 Found {len(mp3_files)} files. Merging with 0.5s-1.0s gaps...")

    try:
        input_streams = []

        for i, f in enumerate(mp3_files):
            # Convert to absolute path for Windows
            file_path = os.path.abspath(f)
            stream = ffmpeg.input(file_path)

            # Add random delay between 500ms and 1000ms (0.5s - 1.0s)
            # We don't need a delay for the very first file (index 0)
            if i > 0:
                delay_ms = random.randint(500, 1000)
                # Apply the adelay filter to both audio channels
                stream = stream.filter("adelay", f"{delay_ms}|{delay_ms}")

            input_streams.append(stream)

        # 3. Concatenate all delayed streams
        joined = ffmpeg.concat(*input_streams, a=1, v=0)

        # 4. Output with high-quality settings
        out = ffmpeg.output(
            joined,
            os.path.abspath(OUTPUT_FILE),
            acodec="libmp3lame",
            audio_bitrate="192k",
        )

        # 5. Run using your specific FFmpeg path
        print(f"🔗 Stitching files into {OUTPUT_FILE}...")
        out.run(cmd=FFMPEG_PATH, overwrite_output=True, quiet=True)

        print(
            f"⭐ SUCCESS! Your natural podcast is ready at: {os.path.abspath(OUTPUT_FILE)}"
        )

    except ffmpeg.Error as e:
        print(f"❌ FFmpeg Error: {e.stderr.decode('utf8') if e.stderr else e}")


if __name__ == "__main__":
    combine_with_random_pauses()
