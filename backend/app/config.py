import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
RESULTS_DIR = DATA_DIR / "results"
DB_PATH = BASE_DIR / "experiments.db"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Greedy vs Beam Search in Indic MT"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Model configuration
    # Default to prajdabre/rotary-indictrans2-indic-en-dist-200M (IndicTrans2 200M distilled)
    # Can also use facebook/nllb-200-distilled-600M or local checkpoint
    DEFAULT_MODEL_NAME: str = os.getenv("MODEL_NAME", "prajdabre/rotary-indictrans2-indic-en-dist-200M")
    FALLBACK_MODEL_NAME: str = "facebook/nllb-200-distilled-600M"
    OLLAMA_MODEL_NAME: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    
    # Device
    DEVICE: str = "cpu"
    
    # Supported Indic Languages mapping
    # Format: ISO/Standard -> (Display Name, IndicTrans/NLLB code)
    SUPPORTED_LANGUAGES: dict = {
        "ta": {"name": "Tamil", "code": "tam_Taml"},
        "hi": {"name": "Hindi", "code": "hin_Deva"},
        "te": {"name": "Telugu", "code": "tel_Telu"},
        "ml": {"name": "Malayalam", "code": "mal_Mlym"},
        "kn": {"name": "Kannada", "code": "kan_Knda"},
        "mr": {"name": "Marathi", "code": "mar_Deva"},
        "bn": {"name": "Bengali", "code": "ben_Beng"},
        "gu": {"name": "Gujarati", "code": "guj_Gujr"},
        "en": {"name": "English", "code": "eng_Latn"}
    }
    
    DEFAULT_SRC_LANG: str = "ta"
    DEFAULT_TGT_LANG: str = "en"
    
    # Decoding configuration defaults
    DEFAULT_MAX_NEW_TOKENS: int = 128
    DEFAULT_BEAM_WIDTH: int = 4
    SUPPORTED_BEAMS: list = [1, 2, 4, 8]
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    SAMPLE_DIR: Path = SAMPLE_DIR
    RESULTS_DIR: Path = RESULTS_DIR
    DB_PATH: Path = DB_PATH

settings = Settings()

# Ensure directories exist
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
