import os

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(BASE_DIR, "instance", "career.db"))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024

WORD2VEC_JOB_VECTOR_PATH = os.getenv(
    "WORD2VEC_JOB_VECTOR_PATH",
    os.path.join(BASE_DIR, "data", "embeddings", "job_vectors_word2vec.pkl"),
)
TEXTCNN_SKILL_MODEL_PATH = os.getenv(
    "TEXTCNN_SKILL_MODEL_PATH",
    os.path.join(BASE_DIR, "data", "models", "skill_predictor.pth"),
)
TEXTCNN_SKILL_PROCESSOR_PATH = os.getenv(
    "TEXTCNN_SKILL_PROCESSOR_PATH",
    os.path.join(BASE_DIR, "data", "models", "skill_text_processor.pkl"),
)
TEXTCNN_SKILL_LABEL_PATH = os.getenv(
    "TEXTCNN_SKILL_LABEL_PATH",
    os.path.join(BASE_DIR, "data", "models", "skill_label_extractor.pkl"),
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")

# local: no external calls. auto: prefer Zhipu, then DeepSeek, then local.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local").lower()
LLM_MODE = os.getenv("LLM_MODE", "auto").lower()
LLM_FORCE_REAL = os.getenv("LLM_FORCE_REAL", "0") == "1"
LLM_MAX_CALLS_PER_RUN = int(os.getenv("LLM_MAX_CALLS_PER_RUN", "1000"))
