import os
import requests
import json
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Retrieve the API key from environment variables
API_KEY = os.getenv("INWORLD_API_KEY")

if not API_KEY:
    print("Error: INWORLD_API_KEY not found in .env file.")
    exit(1)

url = "https://api.inworld.ai/tts/v1/voices"
headers = {"Authorization": f"Basic {API_KEY.strip()}"}

print("Fetching available voices from Inworld...")

try:
    response = requests.get(url, headers=headers)

    # Open the file in write mode ('w')
    with open("list_voices.txt", "w") as f:
        if response.status_code == 200:
            data = response.json()
            # If 'voices' isn't the key, look at the whole response
            voices = data.get("voices", data)

            if isinstance(voices, list):
                f.write(f"Found {len(voices)} voices:\n\n")
                for v in voices:
                    f.write(f"Voice Data: {json.dumps(v, indent=2)}\n")
                    f.write("-" * 30 + "\n")
                print("Successfully saved voice list to list_voices.txt")
            else:
                f.write(f"Unexpected response format: {json.dumps(data, indent=2)}")
                print("Unexpected format received. Check the text file for details.")
        else:
            error_msg = f"Error: {response.status_code} - {response.text}"
            f.write(error_msg)
            print(error_msg)

except Exception as e:
    print(f"An unexpected error occurred: {e}")
