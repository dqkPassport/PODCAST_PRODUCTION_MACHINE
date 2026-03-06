import requests
import base64
import os
import random
import ffmpeg
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# --- INITIALIZATION ---
load_dotenv()
# Using INWORLD_API_KEY from your .env for security
API_KEY = os.getenv("INWORLD_API_KEY")
MODEL_ID = "inworld-tts-1.5-max"

# Your specific Windows path for FFmpeg
FFMPEG_PATH = r"C:\DQK\ffmpeg\bin\ffmpeg.exe"

if not API_KEY:
    print("❌ ERROR: INWORLD_API_KEY not found in .env file!")
    exit()

# Voices chosen for JT and Maddie (American accents)
VOICES = {"JT": "Mark", "Maddie": "Lauren"}

# --- FOLDER SETUP ---
output_dir = Path("inworld")
script_dir = Path("script")

output_dir.mkdir(parents=True, exist_ok=True)
script_dir.mkdir(parents=True, exist_ok=True)


def generate_audio(voice_name, text, filename):
    """Fetches high-quality TTS from Inworld API"""
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
            print(f"❌ API Error for {voice_name}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None


def merge_audio_files(file_list, output_file):
    """Stitches lines and normalizes to -16 LUFS without a report"""
    print(f"\nStitching and normalizing {output_file.name} to -16 LUFS...")
    try:
        input_streams = []
        for f in file_list:
            # Generate random jitter (0.3s to 0.6s) for natural turn-taking
            delay_ms = random.randint(300, 600)
            stream = ffmpeg.input(os.path.abspath(f))

            # Apply 'adelay' filter for natural pauses
            delayed_stream = stream.filter("adelay", f"{delay_ms}|{delay_ms}")
            input_streams.append(delayed_stream)

        # 1. Concatenate all streams
        joined = ffmpeg.concat(*input_streams, a=1, v=0)

        # 2. Apply 'loudnorm' filter to target -16 LUFS
        normalized = joined.filter("loudnorm", i=-16, tp=-1.5, lra=11)

        # 3. Define output and run with your specific FFmpeg path
        out = ffmpeg.output(normalized, os.path.abspath(output_file))
        out.run(overwrite_output=True, quiet=True, cmd=FFMPEG_PATH, capture_stderr=True)

        print(f"⭐ SUCCESS! Podcast ready: {output_file}")

        # Cleanup individual temp files
        for f in file_list:
            if os.path.exists(f):
                os.remove(f)
        print("🧹 Cleanup complete.")

    except ffmpeg.Error as e:
        print(f"❌ FFmpeg Error Output:\n{e.stderr.decode('utf8')}")


def run_podcast_generator():
    """Main loop: Reads script/s1.txt and triggers audio generation"""
    script_file = script_dir / "s1.txt"

    if not script_file.exists():
        print(f"❌ ERROR: Could not find s1.txt in '{script_dir}'!")
        return

    with open(script_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    generated_paths = []
    file_count = 1

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("JT:"):
            speaker, text = "JT", line.replace("JT:", "").strip()
        elif line.startswith("Maddie:"):
            speaker, text = "Maddie", line.replace("Maddie:", "").strip()
        else:
            continue

        filename = f"temp_{file_count:02d}_{speaker}.mp3"
        path = generate_audio(speaker, text, filename)

        if path:
            generated_paths.append(path)
            print(f"✅ Generated: {speaker} line {file_count}")
            file_count += 1

    if generated_paths:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        final_filename = f"final_{timestamp}.mp3"
        final_mp3_path = output_dir / final_filename
        merge_audio_files(generated_paths, final_mp3_path)


if __name__ == "__main__":
    run_podcast_generator()
