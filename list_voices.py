import requests
import json

# Use your working Base64 key
API_KEY = "dWhXNVphQ3R5eWU4aHR5Qzc2S1haMGlFZVBnVjhCS2c6dTdpZkV6MGVLQ0tCc2hLVDZzYVNINERBbmFEZ08zRkFyYWx6VEdRZ0dsU3E4OUFsOUVFM3pMSEM0RUYxamZrQw=="

url = "https://api.inworld.ai/tts/v1/voices"
headers = {"Authorization": f"Basic {API_KEY.strip()}"}

print("Fetching available voices from Inworld...")
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    # If 'voices' isn't the key, let's look at the whole response
    voices = data.get("voices", data)

    if isinstance(voices, list):
        for v in voices:
            # This will print everything so we can find the ID
            print(f"Voice Data: {json.dumps(v, indent=2)}")
            print("-" * 30)
    else:
        print("Unexpected response format:", data)
else:
    print(f"Error: {response.status_code} - {response.text}")
