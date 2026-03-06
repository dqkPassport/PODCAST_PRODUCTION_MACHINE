import requests
import base64
import os
import ffmpeg
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# --- INITIALIZATION ---
load_dotenv()
API_KEY = os.getenv("INWORLD_API_KEY")
MODEL_ID = "inworld-tts-1.5-max"

# YOUR SPECIFIC FFmpeg PATH
FFMPEG_PATH = r"C:\DQK\ffmpeg\bin\ffmpeg.exe"

if not API_KEY:
    print("❌ ERROR: INWORLD_KEY not found in .env file!")
    exit()

VOICES = {"JT": "Edward", "Maddie": "Lauren"}

# --- FOLDER SETUP ---
output_dir = Path("inworld")
script_dir = Path("script")

output_dir.mkdir(parents=True, exist_ok=True)
script_dir.mkdir(parents=True, exist_ok=True)


def generate_audio(voice_name, text, filename):
    url = "https://api.inworld.ai/tts/v1/voice"
    headers = {
        "Authorization": f"Basic {API_KEY.strip()}",
        "Content-Type": "application/json",
    }
    payload = {"text": text, "voiceId": VOICES[voice_name], "modelId": MODEL_ID}

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        audio_data = base64.b64decode(response.json()["audioContent"])
        file_path = output_dir / filename
        with open(file_path, "wb") as f:
            f.write(audio_data)
        return str(file_path)
    else:
        print(f"❌ Error for {voice_name}: {response.text}")
        return None


def merge_audio_files(file_list, output_file):
    print(f"\nStitching lines into {output_file.name}...")
    try:
        input_streams = [ffmpeg.input(f) for f in file_list]
        joined = ffmpeg.concat(*input_streams, a=1, v=0)

        # We pass the cmd argument to point to your specific ffmpeg.exe
        out = ffmpeg.output(joined, str(output_file))
        out.run(overwrite_output=True, quiet=True, cmd=FFMPEG_PATH)

        print(f"⭐ SUCCESS! Your podcast is ready: {output_file}")

        # Cleanup temp files
        for f in file_list:
            os.remove(f)
        print("🧹 Cleanup complete.")

    except ffmpeg.Error as e:
        print(f"❌ FFmpeg Error: {e}")


def run_podcast_generator():
    script_file = script_dir / "s1.txt"

    if not script_file.exists():
        print(f"❌ ERROR: Could not find script.txt in '{script_dir}'!")
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
        # Create a unique filename with the current date and time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        final_filename = f"final_{timestamp}.mp3"
        final_mp3_path = output_dir / final_filename

        merge_audio_files(generated_paths, final_mp3_path)


if __name__ == "__main__":
    run_podcast_generator()
