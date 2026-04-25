"""
Simple file-based cache for AnalysisSchema results.
Keyed by md5(headline) so repeated pipeline runs skip re-analysis
of articles seen in the last `ttl_hours` hours.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from schemas import AnalysisSchema

_CACHE_FILE = Path(__file__).parent / ".analysis_cache.json"
_TTL_SECONDS = 3600  # 1 hour


def _load() -> dict:
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save(data: dict) -> None:
    try:
        _CACHE_FILE.write_text(json.dumps(data))
    except Exception:
        pass


def _key(headline: str) -> str:
    return hashlib.md5(headline.encode()).hexdigest()


def get(headline: str) -> AnalysisSchema | None:
    store = _load()
    entry = store.get(_key(headline))
    if not entry:
        return None
    if time.time() - entry["ts"] > _TTL_SECONDS:
        return None
    try:
        return AnalysisSchema.model_validate(entry["data"])
    except Exception:
        return None


def set(headline: str, analysis: AnalysisSchema) -> None:
    store = _load()
    store[_key(headline)] = {"ts": time.time(), "data": analysis.model_dump()}
    _save(store)


def clear() -> None:
    if _CACHE_FILE.exists():
        _CACHE_FILE.unlink()
