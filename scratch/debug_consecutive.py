import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import torch
from backend.app.services.model_service import model_service
from backend.app.services.translation_service import translation_service
from backend.app.schemas.schemas import TranslateRequest

model_service.load_model()

print("1. Running Greedy...", flush=True)
req_greedy = TranslateRequest(
    source_text="வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
    source_lang="ta",
    target_lang="en",
    decoding_method="greedy",
    beam_width=1,
    max_new_tokens=64
)
t0 = time.time()
res_g = translation_service.translate(req_greedy)
print(f"Greedy finished in {time.time()-t0:.2f}s: {res_g.result.translation}", flush=True)

print("2. Running Beam 4...", flush=True)
req_beam = TranslateRequest(
    source_text="வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
    source_lang="ta",
    target_lang="en",
    decoding_method="beam",
    beam_width=4,
    max_new_tokens=64
)
t0 = time.time()
res_b = translation_service.translate(req_beam)
print(f"Beam 4 finished in {time.time()-t0:.2f}s: {res_b.result.translation}", flush=True)
