import os
import pickle
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from config import BASE_DIR


DEFAULT_WORD2VEC_JOB_VECTOR_PATH = os.path.join(BASE_DIR, "data", "embeddings", "job_vectors_word2vec.pkl")
DEFAULT_TEXTCNN_SKILL_MODEL_PATH = os.path.join(BASE_DIR, "data", "models", "skill_predictor.pth")
DEFAULT_TEXTCNN_SKILL_PROCESSOR_PATH = os.path.join(BASE_DIR, "data", "models", "skill_text_processor.pkl")
DEFAULT_TEXTCNN_SKILL_LABEL_PATH = os.path.join(BASE_DIR, "data", "models", "skill_label_extractor.pkl")


def _word2vec_path() -> str:
    return os.getenv("WORD2VEC_JOB_VECTOR_PATH", DEFAULT_WORD2VEC_JOB_VECTOR_PATH)


def _textcnn_paths() -> Tuple[str, str, str]:
    return (
        os.getenv("TEXTCNN_SKILL_MODEL_PATH", DEFAULT_TEXTCNN_SKILL_MODEL_PATH),
        os.getenv("TEXTCNN_SKILL_PROCESSOR_PATH", DEFAULT_TEXTCNN_SKILL_PROCESSOR_PATH),
        os.getenv("TEXTCNN_SKILL_LABEL_PATH", DEFAULT_TEXTCNN_SKILL_LABEL_PATH),
    )


def _normalize_vectors(vectors) -> np.ndarray:
    array = np.asarray(vectors, dtype=np.float32)
    if array.ndim != 2 or array.size == 0:
        raise ValueError("invalid job vector matrix")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-8, norms)
    return array / norms


@lru_cache(maxsize=4)
def _load_word2vec_artifact(path: str):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = pickle.load(f)
    job_ids = [int(item) for item in data.get("job_ids", [])]
    vectors = _normalize_vectors(data.get("vectors", []))
    if len(job_ids) != len(vectors):
        raise ValueError("job_ids and vectors length mismatch")
    return {
        "job_ids": job_ids,
        "vectors": vectors,
        "raw_names": data.get("raw_names", []),
        "index": {job_id: idx for idx, job_id in enumerate(job_ids)},
    }


def word2vec_available(path: Optional[str] = None) -> bool:
    try:
        return _load_word2vec_artifact(path or _word2vec_path()) is not None
    except Exception:
        return False


def word2vec_similar_jobs(job_id: int, top_k: int = 10, path: Optional[str] = None) -> Optional[List[Dict]]:
    try:
        artifact = _load_word2vec_artifact(path or _word2vec_path())
    except Exception:
        return None
    if not artifact or int(job_id) not in artifact["index"]:
        return None

    idx = artifact["index"][int(job_id)]
    query = artifact["vectors"][idx]
    scores = np.dot(artifact["vectors"], query)
    ranked = np.argsort(scores)[::-1]
    results = []
    seen_names = set()
    raw_names = artifact.get("raw_names") or []
    if idx < len(raw_names):
        seen_names.add(raw_names[idx])

    for candidate_idx in ranked:
        candidate_id = artifact["job_ids"][candidate_idx]
        if candidate_id == int(job_id):
            continue
        candidate_name = raw_names[candidate_idx] if candidate_idx < len(raw_names) else str(candidate_id)
        if candidate_name in seen_names:
            continue
        seen_names.add(candidate_name)
        results.append({
            "job_id": candidate_id,
            "job_name": candidate_name,
            "similarity": round(float(scores[candidate_idx]), 4),
        })
        if len(results) >= top_k:
            break
    return results


def _row_similarity_from_word2vec(source_id: int, rows: Sequence) -> Optional[Dict[int, float]]:
    ids = [int(row["id"] if "id" in row.keys() else row["job_id"]) for row in rows]
    top_k = max(len(ids), 1)
    results = word2vec_similar_jobs(source_id, top_k=top_k)
    if results is None:
        return None
    wanted = set(ids)
    return {item["job_id"]: item["similarity"] for item in results if item["job_id"] in wanted}


def rank_rows_with_word2vec(source_id: int, rows: Sequence) -> Optional[List[Tuple[object, float]]]:
    score_map = _row_similarity_from_word2vec(source_id, rows)
    if score_map is None:
        return None
    ranked = []
    for row in rows:
        row_id = int(row["id"] if "id" in row.keys() else row["job_id"])
        if row_id in score_map:
            ranked.append((row, score_map[row_id]))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked


@lru_cache(maxsize=2)
def _load_skill_predictor(model_path: str, processor_path: str, label_path: str):
    if not all(os.path.exists(path) for path in [model_path, processor_path, label_path]):
        return None
    from services.dl_models.skill_predictor_model import SkillPredictor

    return SkillPredictor(model_path, processor_path, label_path)


def predict_skills_with_textcnn(text: str, top_k: int = 5) -> Tuple[List[Dict], str]:
    try:
        predictor = _load_skill_predictor(*_textcnn_paths())
        if predictor is None:
            return [], "rules"
        predictions = predictor.predict(text, top_k=top_k)
        return predictions, "textcnn"
    except Exception:
        return [], "rules"
