from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).parent.parent / "data" / "crop_diseases.json"
_records: list[dict] | None = None


def _load() -> list[dict]:
    global _records
    if _records is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _records = json.load(f)
        logger.info("knowledge base loaded: %d records", len(_records))
    return _records


def retrieve(crop_name: str, problem_description: str, top_k: int = 2) -> list[dict]:
    records = _load()
    crop = crop_name.lower().strip()
    problem = problem_description.lower().strip()

    scored: list[tuple[int, dict]] = []
    for record in records:
        score = 0

        # Crop name match (primary signal — high weight)
        record_crop = record["crop"].lower()
        aliases = [a.lower() for a in record.get("crop_aliases", [])]
        if crop == record_crop or crop in aliases:
            score += 10
        elif record_crop in crop or any(a in crop for a in aliases):
            score += 6

        # Skip entirely if no crop overlap — keeps results relevant
        if score == 0:
            continue

        # Disease name mentioned in the problem
        if record["disease"].lower() in problem:
            score += 5

        # Keyword matches in the problem description
        for kw in record.get("keywords", []):
            if kw.lower() in problem:
                score += 2

        # Partial symptom word matches (words longer than 4 chars to avoid noise)
        for symptom in record.get("symptoms", []):
            for word in symptom.lower().split():
                if len(word) > 4 and word in problem:
                    score += 1
                    break  # one point per symptom, not per word

        scored.append((score, record))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_k]]


def format_context(records: list[dict]) -> str:
    if not records:
        return ""

    parts = ["Relevant records from curated Indian agricultural knowledge base:"]
    for r in records:
        parts.append(
            f"\n[{r['crop'].title()} — {r['disease']}]\n"
            f"Cause: {r['cause']}\n"
            f"Key symptoms: {'; '.join(r['symptoms'][:3])}\n"
            f"Recommended treatment: {'; '.join(r['treatment_en'])}\n"
            f"Prevention: {r['prevention']}\n"
            f"Common in: {r['region']}"
        )
    return "\n".join(parts)
