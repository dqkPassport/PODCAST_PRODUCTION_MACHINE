import ffmpeg
import os

# Your specific Windows path for FFmpeg
FFMPEG_PATH = r"C:\DQK\ffmpeg\bin\ffmpeg.exe"


def create_10s_silence(output_filename):
    print(f"Generating 10 seconds of silence...")

    try:
        # anullsrc creates a null (silent) audio source
        # r=44100 sets the sample rate
        # cl=stereo sets it to 2 channels
        silence = ffmpeg.input("anullsrc=r=44100:cl=stereo", f="lavfi", t=10)

        # Output to mp3
        out = ffmpeg.output(silence, output_filename, acodec="libmp3lame")

        # Run using your specific FFmpeg path
        out.run(cmd=FFMPEG_PATH, overwrite_output=True, quiet=True)

        print(f"⭐ SUCCESS! Created: {os.path.abspath(output_filename)}")

    except ffmpeg.Error as e:
        print(f"❌ FFmpeg Error: {e.stderr.decode('utf8')}")


if __name__ == "__main__":
    create_10s_silence("silence_10s.mp3")
