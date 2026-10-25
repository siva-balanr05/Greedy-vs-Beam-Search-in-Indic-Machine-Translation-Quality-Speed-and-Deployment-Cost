import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
from backend.app.services.model_service import model_service
from backend.app.services.translation_service import translation_service
from backend.app.schemas.schemas import CompareRequest

print("Loading model...", flush=True)
model_service.load_model()

req = CompareRequest(
    source_text="வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
    source_lang="ta",
    target_lang="en",
    beam_width=4,
    max_new_tokens=64,
    reference_text="Hello, how are you?"
)

print("Calling compare()...", flush=True)
t0 = time.time()
res = translation_service.compare(req)
print(f"Compare done in {time.time()-t0:.2f}s!", flush=True)
print("Greedy Translation:", res.greedy.translation)
print("Greedy BLEU:", res.greedy.sentence_bleu)
print("Greedy chrF:", res.greedy.sentence_chrf)
print("Beam Translation:", res.beam.translation)
print("Beam BLEU:", res.beam.sentence_bleu)
print("Beam chrF:", res.beam.sentence_chrf)
print("Latency Difference (ms):", res.latency_difference_ms)
print("Latency Ratio:", res.latency_ratio)
