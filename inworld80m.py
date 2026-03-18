import requests
import base64
import os
import random
import ffmpeg
import hashlib
import shutil
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

# --- INITIALIZATION ---
load_dotenv()
API_KEY = os.getenv("INWORLD_API_KEY")
MODEL_ID = "inworld-tts-1.5-max"
FFMPEG_PATH = r"C:\DQK\ffmpeg\bin\ffmpeg.exe"
VOICE_ID = "Jonah"  # Fixed to Jonah

if not API_KEY:
    print("❌ ERROR: INWORLD_API_KEY not found in .env file!")
    exit()

# --- FOLDER SETUP ---
output_dir = Path("inworld")
script_dir = Path("script")
cache_dir = Path("cache")

for folder in [output_dir, script_dir, cache_dir]:
    folder.mkdir(parents=True, exist_ok=True)


def get_text_hash(text):
    """Hash based on text and the specific Jonah voice."""
    combined_string = f"{VOICE_ID}:{text}"
    return hashlib.md5(combined_string.encode()).hexdigest()


def generate_audio(text, filename):
    url = "https://api.inworld.ai/tts/v1/voice"
    headers = {
        "Authorization": f"Basic {API_KEY.strip()}",
        "Content-Type": "application/json",
    }
    payload = {"text": text, "voiceId": VOICE_ID, "modelId": MODEL_ID}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            audio_data = base64.b64decode(response.json()["audioContent"])
            file_path = output_dir / filename
            with open(file_path, "wb") as f:
                f.write(audio_data)
            return str(file_path)
        else:
            print(f"\n❌ API Error: {response.text}")
            return None
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        return None


def merge_audio_files(file_list, output_file):
    try:
        input_streams = []
        for f in file_list:
            # Slight delay between paragraphs for a natural pace
            delay_ms = random.randint(400, 700)
            stream = ffmpeg.input(os.path.abspath(f))

            # Apply 80% speed (atempo=0.8) as per your original logic
            slowed_stream = stream.filter("atempo", 0.8)
            delayed_stream = slowed_stream.filter("adelay", f"{delay_ms}|{delay_ms}")
            input_streams.append(delayed_stream)

        joined = ffmpeg.concat(*input_streams, a=1, v=0)
        normalized = joined.filter("loudnorm", i=-16, tp=-1.5, lra=11)

        out = ffmpeg.output(normalized, os.path.abspath(output_file))
        out.run(overwrite_output=True, quiet=True, cmd=FFMPEG_PATH, capture_stderr=True)

        # Cleanup temp files
        for f in file_list:
            if os.path.exists(f) and "temp_" in f:
                os.remove(f)
        return True
    except ffmpeg.Error as e:
        print(f"❌ FFmpeg Error Output:\n{e.stderr.decode('utf8')}")
        return False


def run_generator(script_filename, dry_run=False):
    script_path = script_dir / script_filename

    if not script_path.exists():
        print(f"❌ ERROR: {script_filename} not found in '{script_dir}'!")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        # Filter out empty lines
        lines = [line.strip() for line in f if line.strip()]

    print(f"📖 Jonah is reading: {script_filename} ({len(lines)} lines)")

    generated_paths = []

    for i, line in enumerate(
        tqdm(lines, desc="🎙️ Generating Jonah's Audio", unit="line")
    ):
        # Clean the text: Remove "Name: " prefix if it exists
        clean_text = line
        if ":" in line[:15]:  # Look for a colon in the first 15 characters
            clean_text = line.split(":", 1)[1].strip()

        if dry_run:
            continue

        # --- SMART CACHE SYSTEM ---
        line_hash = get_text_hash(clean_text)
        cache_path = cache_dir / f"{line_hash}.mp3"
        temp_filename = f"temp_{i:03d}_jonah.mp3"
        temp_path = output_dir / temp_filename

        if cache_path.exists():
            shutil.copy(cache_path, temp_path)
            generated_paths.append(str(temp_path))
        else:
            path = generate_audio(clean_text, temp_filename)
            if path:
                shutil.copy(path, cache_path)
                generated_paths.append(path)

    if not dry_run and generated_paths:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        final_filename = f"jonah_{script_path.stem}_{timestamp}.mp3"
        final_path = output_dir / final_filename

        if merge_audio_files(generated_paths, final_path):
            print(f"\n⭐ SUCCESS! Jonah's narration is ready: {final_path}")


if __name__ == "__main__":
    target_script = sys.argv[1] if len(sys.argv) > 1 else "s1.txt"
    is_dry = "--dry" in sys.argv

    run_generator(target_script, dry_run=is_dry)
