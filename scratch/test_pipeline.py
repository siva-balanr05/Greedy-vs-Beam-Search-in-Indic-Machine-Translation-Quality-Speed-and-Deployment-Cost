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

model_service.load_model()
ip = IndicProcessor(inference=True)

text = "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?"
src_code = "tam_Taml"
tgt_code = "eng_Latn"

batch = ip.preprocess_batch([text], src_lang=src_code, tgt_lang=tgt_code)
inputs = model_service.tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
inputs = {k: v.to(model_service.device) for k, v in inputs.items()}

# 1. Greedy
print("Running Greedy...")
t0 = time.perf_counter()
with torch.no_grad():
    greedy_out = model_service.model.generate(
        **inputs,
        num_beams=1,
        do_sample=False,
        max_new_tokens=30,
        use_cache=False
    )
print(f"Greedy finished in {time.perf_counter()-t0:.2f}s, tokens={greedy_out.shape[1]}")
dec = ip.postprocess_batch(model_service.tokenizer.batch_decode(greedy_out, skip_special_tokens=True), lang=tgt_code)
print(f"Greedy translation: {dec[0]}")

# 2. Beam 2
print("Running Beam 2...")
t0 = time.perf_counter()
with torch.no_grad():
    b2_out = model_service.model.generate(
        **inputs,
        num_beams=2,
        do_sample=False,
        max_new_tokens=30,
        early_stopping=True,
        use_cache=False
    )
print(f"Beam 2 finished in {time.perf_counter()-t0:.2f}s, tokens={b2_out.shape[1]}")
dec2 = ip.postprocess_batch(model_service.tokenizer.batch_decode(b2_out, skip_special_tokens=True), lang=tgt_code)
print(f"Beam 2 translation: {dec2[0]}")

# 3. Beam 4
print("Running Beam 4...")
t0 = time.perf_counter()
with torch.no_grad():
    b4_out = model_service.model.generate(
        **inputs,
        num_beams=4,
        do_sample=False,
        max_new_tokens=30,
        early_stopping=True,
        use_cache=False
    )
print(f"Beam 4 finished in {time.perf_counter()-t0:.2f}s, tokens={b4_out.shape[1]}")
dec4 = ip.postprocess_batch(model_service.tokenizer.batch_decode(b4_out, skip_special_tokens=True), lang=tgt_code)
print(f"Beam 4 translation: {dec4[0]}")
