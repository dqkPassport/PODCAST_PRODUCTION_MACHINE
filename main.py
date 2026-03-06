import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from openai import OpenAI

# ==========================================
# 1️⃣ Setup
# ==========================================

load_dotenv()
client = OpenAI()

output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

ffmpeg_path = r"C:\DQK\ffmpeg\bin\ffmpeg.exe"  # adjust if needed

# ==========================================
# 2️⃣ Script
# ==========================================

script = """
JT: Exactly. (chuckle) And I think everyone thinks they need grammar books… but that’s not true.
Maddie: Totally! Speaking is about practice, not rules. Even talking to yourself counts.
JT: (laugh) I do that all the time. Sometimes I practice dialogues in my car.
Maddie: Same! Or when I’m cooking, I repeat phrases or sentences out loud. It feels silly, but it works.

"""

VOICE_MAP = {
    "JT": "cedar",
    "Maddie": "marin",
}

# ==========================================
# 3️⃣ Parse Script
# ==========================================


def parse_script(script_text):
    pattern = r"(JT|Maddie):\s*(.*?)(?=\n(?:JT|Maddie):|$)"
    return re.findall(pattern, script_text, re.S)


# ==========================================
# 4️⃣ Generate TTS
# ==========================================


def generate_tts_block(speaker, text, index):
    filename = os.path.join(output_folder, f"block_{index:03d}_{speaker}.mp3")
    print(f"Generating {speaker}...")

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=VOICE_MAP[speaker],
        input=text.strip(),
    ) as response:
        response.stream_to_file(filename)

    return filename


# ==========================================
# 5️⃣ Merge Audio
# ==========================================


def merge_audio_files(audio_files, output_file):
    list_path = os.path.join(output_folder, "file_list.txt")

    with open(list_path, "w", encoding="utf-8") as f:
        for file in sorted(audio_files):
            full_path = os.path.abspath(file).replace("\\", "/")
            f.write(f"file '{full_path}'\n")

    subprocess.run(
        [
            ffmpeg_path,
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
            "-y",
            output_file,
        ],
        check=True,
    )

    os.remove(list_path)


# ==========================================
# 6️⃣ Normalize to -16 LUFS
# ==========================================


def normalize_lufs(input_file, output_file):
    print("Normalizing to -16 LUFS...")

    subprocess.run(
        [
            ffmpeg_path,
            "-i",
            input_file,
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            "-y",
            output_file,
        ],
        check=True,
    )


# ==========================================
# 7️⃣ Main
# ==========================================


def main():
    print("🚀 Passport Podcast Engine Starting...\n")

    lines = parse_script(script)

    if not lines:
        print("No script content found.")
        return

    # Generate TTS in parallel
    audio_files = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for i, (speaker, text) in enumerate(lines):
            futures.append(executor.submit(generate_tts_block, speaker, text, i))

        for future in futures:
            audio_files.append(future.result())

    # Merge
    merged_file = os.path.join(output_folder, "part.mp3")
    merge_audio_files(audio_files, merged_file)

    # Normalize
    normalized_file = os.path.join(output_folder, "partLUFS.mp3")
    normalize_lufs(merged_file, normalized_file)

    print("\n✅ Done!")
    print("Raw file:      ", merged_file)
    print("Normalized:    ", normalized_file)


if __name__ == "__main__":
    main()
