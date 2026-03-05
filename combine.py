import os
import random
import subprocess

# ===== SETTINGS =====
INPUT_FOLDER = "final"
OUTPUT_FILE = "final.mp3"

USE_RANDOM_PAUSES = True
MIN_PAUSE = 0.4
MAX_PAUSE = 0.7

# ====================

files = sorted(
    f for f in os.listdir(INPUT_FOLDER) if f.endswith(".mp3") and f != OUTPUT_FILE
)

if not files:
    print("❌ No MP3 files found.")
    exit()

list_path = os.path.join(INPUT_FOLDER, "list.txt")
silence_files = []

print("Preparing files...")

# Create silence files if enabled
if USE_RANDOM_PAUSES and len(files) > 1:
    for i in range(len(files) - 1):
        duration = round(random.uniform(MIN_PAUSE, MAX_PAUSE), 2)

        silence_name = f"pause_{i}.mp3"
        silence_path = os.path.join(INPUT_FOLDER, silence_name)

        subprocess.run(
            [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=stereo",
                "-t",
                str(duration),
                "-q:a",
                "9",
                "-acodec",
                "libmp3lame",
                silence_path,
                "-y",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        silence_files.append(silence_name)

        print(f"Pause {i}: {duration}s")


# Create concat list
with open(list_path, "w", encoding="utf-8") as f:
    for i, file in enumerate(files):
        path = os.path.abspath(os.path.join(INPUT_FOLDER, file)).replace("\\", "/")
        f.write(f"file '{path}'\n")

        if USE_RANDOM_PAUSES and i < len(silence_files):
            silence_path = os.path.abspath(
                os.path.join(INPUT_FOLDER, silence_files[i])
            ).replace("\\", "/")

            f.write(f"file '{silence_path}'\n")


print("Merging audio...")

subprocess.run(
    [
        "ffmpeg",
        "-fflags",
        "+genpts",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-c:a",
        "libmp3lame",
        "-b:a",
        "192k",
        "-avoid_negative_ts",
        "make_zero",
        os.path.join(INPUT_FOLDER, OUTPUT_FILE),
        "-y",
    ],
    check=True,
)

# Cleanup
os.remove(list_path)

for s in silence_files:
    os.remove(os.path.join(INPUT_FOLDER, s))

print("\n✅ Done!")
print(f"Created: {INPUT_FOLDER}/{OUTPUT_FILE}")
