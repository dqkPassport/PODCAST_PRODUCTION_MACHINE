# python inworld85.py s1.txt


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

if not API_KEY:
    print("❌ ERROR: INWORLD_API_KEY not found in .env file!")
    exit()

# If you change these names (e.g., "Timothy" to "Edward"), the cache will now reset automatically.
VOICES = {"JT": "Timothy", "Maddie": "Lauren"}

# --- FOLDER SETUP ---
output_dir = Path("inworld")
script_dir = Path("script")
cache_dir = Path("cache")

for folder in [output_dir, script_dir, cache_dir]:
    folder.mkdir(parents=True, exist_ok=True)


def get_text_hash(text, speaker):
    """
    Improved hashing: Now includes the Voice ID.
    If you change the voice in the VOICES dict, it generates a new hash.
    """
    voice_id = VOICES.get(speaker, "default")
    combined_string = f"{speaker}:{voice_id}:{text}"
    return hashlib.md5(combined_string.encode()).hexdigest()


def generate_audio(voice_name, text, filename):
    url = "https://api.inworld.ai/tts/v1/voice"
    headers = {
        "Authorization": f"Basic {API_KEY.strip()}",
        "Content-Type": "application/json",
    }
    payload = {"text": text, "voiceId": VOICES[voice_name], "modelId": MODEL_ID}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            audio_data = base64.b64decode(response.json()["audioContent"])
            file_path = output_dir / filename
            with open(file_path, "wb") as f:
                f.write(audio_data)
            return str(file_path)
        else:
            print(f"\n❌ API Error for {voice_name}: {response.text}")
            return None
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        return None


def merge_audio_files(file_list, output_file):
    try:
        input_streams = []
        for f in file_list:
            # Random delay between lines for natural conversation
            delay_ms = random.randint(400, 800)
            stream = ffmpeg.input(os.path.abspath(f))

            # Apply 85% speed (atempo=0.85) for English learners
            slowed_stream = stream.filter("atempo", 0.8)
            delayed_stream = slowed_stream.filter("adelay", f"{delay_ms}|{delay_ms}")
            input_streams.append(delayed_stream)

        joined = ffmpeg.concat(*input_streams, a=1, v=0)
        normalized = joined.filter("loudnorm", i=-16, tp=-1.5, lra=11)

        out = ffmpeg.output(normalized, os.path.abspath(output_file))
        out.run(overwrite_output=True, quiet=True, cmd=FFMPEG_PATH, capture_stderr=True)

        # Cleanup temp files (keeping the cache safe)
        for f in file_list:
            if os.path.exists(f) and "temp_" in f:
                os.remove(f)
        return True
    except ffmpeg.Error as e:
        print(f"❌ FFmpeg Error Output:\n{e.stderr.decode('utf8')}")
        return False


def run_podcast_generator(script_filename, dry_run=False):
    script_path = script_dir / script_filename

    if not script_path.exists():
        print(f"❌ ERROR: {script_filename} not found in '{script_dir}'!")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"📖 Processing: {script_filename} ({len(lines)} lines)")
    if dry_run:
        print("🧪 MODE: DRY RUN (No credits will be used)")

    generated_paths = []

    # --- PROGRESS BAR ---
    for i, line in enumerate(tqdm(lines, desc="🎙️ Generating Audio", unit="line")):
        if line.startswith("JT:"):
            speaker, text = "JT", line.replace("JT:", "").strip()
        elif line.startswith("Maddie:"):
            speaker, text = "Maddie", line.replace("Maddie:", "").strip()
        else:
            continue

        if dry_run:
            continue

        # --- SMART CACHE SYSTEM ---
        line_hash = get_text_hash(text, speaker)
        cache_path = cache_dir / f"{line_hash}.mp3"
        temp_filename = f"temp_{i:02d}_{speaker}.mp3"
        temp_path = output_dir / temp_filename

        if cache_path.exists():
            # If the specific voice + text combo exists, use it
            shutil.copy(cache_path, temp_path)
            generated_paths.append(str(temp_path))
        else:
            # Otherwise, call the API for the new voice
            path = generate_audio(speaker, text, temp_filename)
            if path:
                shutil.copy(path, cache_path)  # Save to cache for next time
                generated_paths.append(path)

    if not dry_run and generated_paths:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        final_filename = f"final_{script_path.stem}_{timestamp}.mp3"
        final_path = output_dir / final_filename

        if merge_audio_files(generated_paths, final_path):
            print(f"\n⭐ SUCCESS! New voices are ready: {final_path}")
    elif dry_run:
        print(f"\n✅ Dry run complete. {len(lines)} lines validated.")


if __name__ == "__main__":
    target_script = sys.argv[1] if len(sys.argv) > 1 else "s1.txt"
    is_dry = "--dry" in sys.argv

    run_podcast_generator(target_script, dry_run=is_dry)
