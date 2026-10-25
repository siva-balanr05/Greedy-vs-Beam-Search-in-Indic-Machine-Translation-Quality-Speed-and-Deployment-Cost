# Forward compatibility with modern transformers (v4.36+ / v5.x) for IndicTransToolkit
try:
    import transformers.tokenization_utils
    import transformers.tokenization_utils_base
    if not hasattr(transformers.tokenization_utils, "PreTrainedTokenizerBase"):
        transformers.tokenization_utils.PreTrainedTokenizerBase = transformers.tokenization_utils_base.PreTrainedTokenizerBase
except Exception:
    pass

