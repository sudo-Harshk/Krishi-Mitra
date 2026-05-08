from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from .schemas import DiagnoseRequest, DiagnoseResponse

DEFAULT_MODEL = "gemma-4-26b-a4-b-it"


def _fallback_diagnosis(request: DiagnoseRequest, image_received: bool) -> DiagnoseResponse:
    crop = request.crop_name.strip()
    issue = request.problem_description.strip()

    return DiagnoseResponse(
        summary_en=f"Likely crop issue detected for {crop}.",
        summary_te=f"{crop} పంటకు సంభవించే సమస్యను గుర్తించాం.",
        likely_issue=issue,
        action_steps_en=[
            "Inspect leaves and stems closely.",
            "Remove visibly affected parts if safe.",
            "Follow label guidance before spraying anything.",
        ],
        action_steps_te=[
            "ఆకులు మరియు కాండాన్ని దగ్గరగా పరిశీలించండి.",
            "సురక్షితం అయితే ప్రభావిత భాగాలను తొలగించండి.",
            "ఏదైనా పిచికారీ చేసే ముందు లేబుల్ సూచనలు పాటించండి.",
        ],
        weather_warning_en="Check the forecast before spraying if location is provided.",
        weather_warning_te="స్థానం ఇచ్చినట్లయితే పిచికారీకి ముందు వాతావరణ సూచనను తనిఖీ చేయండి.",
        confidence=0.35,
        source_notes=[
            "Fallback response used because Gemini API was unavailable",
            "Provide GOOGLE_API_KEY to enable Gemma output",
        ],
        image_received=image_received,
    )


def _load_json_from_text(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    return json.loads(text)


def _build_prompt(request: DiagnoseRequest) -> str:
    location = request.location.strip() if request.location else ""
    return f"""
You are Krishi Mitra, an expert agricultural assistant for Indian farmers.
Return ONLY valid JSON with these keys:
- summary_en: string
- summary_te: string
- likely_issue: string
- action_steps_en: array of strings
- action_steps_te: array of strings
- weather_warning_en: string or null
- weather_warning_te: string or null
- confidence: number from 0 to 1
- source_notes: array of strings

Rules:
- Be practical, safe, and concise.
- Use simple English.
- Use clear Telugu translations.
- Do not mention internal policy or hidden reasoning.
- If the diagnosis is uncertain, say so plainly and lower confidence.
- If weather matters, give a clear spraying or irrigation caution.

User input:
- Crop: {request.crop_name.strip()}
- Problem: {request.problem_description.strip()}
- Location: {location or "not provided"}
""".strip()


def _coerce_response(data: dict[str, Any], image_received: bool) -> DiagnoseResponse:
    return DiagnoseResponse(
        summary_en=str(data.get("summary_en", "")).strip() or "Diagnosis unavailable.",
        summary_te=str(data.get("summary_te", "")).strip() or "నిర్ధారణ అందుబాటులో లేదు.",
        likely_issue=str(data.get("likely_issue", "")).strip() or "Unknown issue",
        action_steps_en=[str(item) for item in data.get("action_steps_en", [])][:5],
        action_steps_te=[str(item) for item in data.get("action_steps_te", [])][:5],
        weather_warning_en=(
            str(data["weather_warning_en"]).strip()
            if data.get("weather_warning_en") not in (None, "")
            else None
        ),
        weather_warning_te=(
            str(data["weather_warning_te"]).strip()
            if data.get("weather_warning_te") not in (None, "")
            else None
        ),
        confidence=max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
        source_notes=[str(item) for item in data.get("source_notes", [])][:5],
        image_received=image_received,
    )


def _run_gemini(
    request: DiagnoseRequest,
    image_path: Path | None,
    image_content_type: str | None,
) -> DiagnoseResponse:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return _fallback_diagnosis(request, image_path is not None)

    model = os.getenv("GEMMA_MODEL", DEFAULT_MODEL)
    client = genai.Client(api_key=api_key)
    prompt = _build_prompt(request)
    contents: list[Any] = [prompt]

    if image_path is not None:
        uploaded = client.files.upload(
            file=str(image_path),
            config={"mimeType": image_content_type or "image/jpeg"},
        )
        contents = [uploaded, prompt]

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="high"),
            system_instruction=(
                "You are a production agricultural assistant. "
                "Return only JSON, never markdown."
            ),
        ),
    )

    if not response.text:
        return _fallback_diagnosis(request, image_path is not None)

    try:
        parsed = _load_json_from_text(response.text)
    except json.JSONDecodeError:
        return _fallback_diagnosis(request, image_path is not None)

    return _coerce_response(parsed, image_path is not None)


def generate_diagnosis(
    request: DiagnoseRequest,
    image_bytes: bytes | None,
    image_filename: str | None,
    image_content_type: str | None,
) -> DiagnoseResponse:
    crop = request.crop_name.strip()
    if not crop:
        return _fallback_diagnosis(request, image_bytes is not None)

    image_path: Path | None = None
    temp_file: tempfile.NamedTemporaryFile | None = None

    try:
        if image_bytes is not None:
            suffix = Path(image_filename or "upload.jpg").suffix or ".jpg"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(image_bytes)
            temp_file.flush()
            temp_file.close()
            image_path = Path(temp_file.name)

        return _run_gemini(request, image_path, image_content_type)
    except Exception:
        return _fallback_diagnosis(request, image_bytes is not None)
    finally:
        if temp_file is not None:
            try:
                Path(temp_file.name).unlink(missing_ok=True)
            except OSError:
                pass
