import sys
import time
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import transformers.tokenization_utils
import transformers.tokenization_utils_base
if not hasattr(transformers.tokenization_utils, "PreTrainedTokenizerBase"):
    transformers.tokenization_utils.PreTrainedTokenizerBase = transformers.tokenization_utils_base.PreTrainedTokenizerBase

from IndicTransToolkit import IndicProcessor
from backend.app.services.model_service import model_service

print("Loading model...", flush=True)
model_service.load_model()
print("Model loaded.", flush=True)

ip = IndicProcessor(inference=True)
text = "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?"
batch = ip.preprocess_batch([text], src_lang="tam_Taml", tgt_lang="eng_Latn")
inputs = model_service.tokenizer(batch, return_tensors="pt")
inputs = {k: v.to(model_service.device) for k, v in inputs.items()}
print("Inputs prepared:", inputs, flush=True)

print("Starting beam search with num_beams=2, max_new_tokens=10...", flush=True)
t0 = time.time()
with torch.no_grad():
    out = model_service.model.generate(
        **inputs,
        num_beams=2,
        max_new_tokens=10,
        do_sample=False,
        use_cache=False
    )
print(f"Beam search finished in {time.time()-t0:.2f}s: {out}", flush=True)
