# No silence gaps between segments


import os
import ffmpeg
from pathlib import Path

# --- CONFIGURATION ---
# Your specific Windows path for FFmpeg
FFMPEG_PATH = r"C:\DQK\ffmpeg\bin\ffmpeg.exe"
INPUT_DIR = Path("inworld")
# Now targeting the 'final' folder
OUTPUT_DIR = Path("final")
OUTPUT_FILE = OUTPUT_DIR / "final.mp3"


def combine_podcast_files():
    # 1. Ensure the 'final' output folder exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Get all mp3 files from 'inworld' and sort them numerically
    # This ensures 01.mp3, 02.mp3, etc., stay in order
    mp3_files = sorted(
        [f for f in INPUT_DIR.glob("*.mp3") if f.name != "final.mp3"],
        key=lambda x: x.name,
    )

    if not mp3_files:
        print(f"❌ No .mp3 files found in {INPUT_DIR}")
        return

    print(f"📚 Found {len(mp3_files)} files in '{INPUT_DIR}'. Starting merge...")

    try:
        # 3. Prepare the input streams using absolute paths for Windows stability
        input_streams = [ffmpeg.input(os.path.abspath(f)) for f in mp3_files]

        # 4. Concatenate streams (a=1 for audio, v=0 for no video)
        joined = ffmpeg.concat(*input_streams, a=1, v=0)

        # 5. Output with high-quality MP3 settings
        out = ffmpeg.output(
            joined,
            os.path.abspath(OUTPUT_FILE),
            acodec="libmp3lame",
            audio_bitrate="192k",
        )

        # 6. Run the command using your specific FFmpeg path
        print(f"🔗 Stitching files into {OUTPUT_FILE}...")
        out.run(cmd=FFMPEG_PATH, overwrite_output=True, quiet=True)

        print(
            f"⭐ SUCCESS! Your merged podcast is ready at: {os.path.abspath(OUTPUT_FILE)}"
        )

    except ffmpeg.Error as e:
        # Decodes the FFmpeg error log so you can debug if something goes wrong
        print(f"❌ FFmpeg Error: {e.stderr.decode('utf8') if e.stderr else e}")


if __name__ == "__main__":
    combine_podcast_files()
