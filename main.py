import os
import re
import subprocess
import random
from dotenv import load_dotenv
from openai import OpenAI

# 1️⃣ Load API key
load_dotenv()
client = OpenAI()

# 2️⃣ Example script (replace with full 15-min script later)
script = """
Walker:  Hey Maddie, today we’re talking about confidence.
Maddie: (chuckle) (Haha) Oh I love this topic...!
Walker: Confidence is something you build step by step.
Maddie: (laughing) (chuckle) Yes! You don’t need perfect grammar.
"""

# 3️⃣ Voices
VOICE_MAP = {
    "Walker": "cedar",  # male
    "Maddie": "marin",  # female
}

# 4️⃣ Output folder
output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

# 5️⃣ Path to ffmpeg.exe (update to your installation)
ffmpeg_path = r"C:\DQK\ffmpeg\bin\ffmpeg.exe"


# 6️⃣ Function to generate TTS for each line
def generate_audio(text, voice, filename):
    print(f"Generating {voice} voice for: {text}")
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts", voice=voice, input=text
    ) as response:
        response.stream_to_file(filename)


# 7️⃣ Split text by sentences for natural pauses
def split_text_with_pauses(text):
    sentences = re.split(r"([.!?])", text)
    chunks = []
    for i in range(0, len(sentences) - 1, 2):
        chunk = sentences[i].strip() + sentences[i + 1]
        chunks.append(chunk)
    return chunks


# 8️⃣ Generate a tiny random silence MP3
def generate_silence(filename, duration):
    subprocess.run(
        [
            ffmpeg_path,
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=stereo",
            "-t",
            str(duration),
            "-q:a",
            "9",
            "-y",
            filename,
        ],
        check=True,
    )


# 9️⃣ Parse the script
lines = re.findall(r"(Walker|Maddie): (.+)", script)
audio_files = []

for i, (speaker, text) in enumerate(lines):
    for j, sentence in enumerate(split_text_with_pauses(text)):
        # 9a️⃣ Generate TTS for each sentence
        line_file = os.path.join(output_folder, f"line_{i}_{j}.mp3")
        generate_audio(sentence, VOICE_MAP[speaker], line_file)
        audio_files.append(line_file)

        # 9b️⃣ Add random micro-pause after each sentence (0.1-0.3s)
        silence_duration = round(random.uniform(0.1, 0.3), 2)
        silence_file = os.path.join(output_folder, f"silence_{i}_{j}.mp3")
        generate_silence(silence_file, silence_duration)
        audio_files.append(silence_file)

# 10️⃣ Create file list for FFmpeg concat
final_list_file = os.path.join(output_folder, "file_list.txt")
with open(final_list_file, "w") as f:
    for file in audio_files:
        f.write(f"file '{os.path.abspath(file)}'\n")

# 11️⃣ Merge all lines into one final episode
final_output = os.path.join(output_folder, "final_episode.mp3")
subprocess.run(
    [
        ffmpeg_path,
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        final_list_file,
        "-c:a",
        "mp3",
        "-b:a",
        "192k",
        "-y",
        final_output,
    ],
    check=True,
)

print("✅ Episode created successfully at:", final_output)
