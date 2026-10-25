import requests
import json

payload = {
    "source_text": "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
    "source_lang": "ta",
    "target_lang": "en",
    "beam_width": 4,
    "max_new_tokens": 64
}

res = requests.post("http://127.0.0.1:8000/api/translate/compare", json=payload, timeout=60)
print("Status:", res.status_code)
print(json.dumps(res.json(), indent=2))
