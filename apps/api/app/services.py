from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import requests
from google import genai
from google.genai import types

from .knowledge import format_context, retrieve
from .schemas import DiagnoseRequest, DiagnoseResponse

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemma-4-26b-a4b-it"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Tool declaration — Gemma decides when to call this based on context
_WEATHER_FUNCTION = {
    "name": "get_weather",
    "description": (
        "Returns current weather conditions for a farming location. "
        "Call this when the farmer has provided a location and weather conditions "
        "may affect treatment decisions such as spraying or irrigation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City or district name, e.g. 'Warangal, Telangana' or 'Guntur'",
            }
        },
        "required": ["location"],
    },
}


def _fallback_diagnosis(
    request: DiagnoseRequest,
    image_received: bool,
    weather_warning: str | None = None,
    weather_summary: str | None = None,
) -> DiagnoseResponse:
    crop = request.crop_name.strip()
    issue = request.problem_description.strip()

    notes = [
        "Fallback response used because Gemini API was unavailable",
        "Provide GOOGLE_API_KEY to enable Gemma output",
    ]
    if weather_summary:
        notes.append(weather_summary)

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
        weather_warning_en=weather_warning
        or "Check the forecast before spraying if location is provided.",
        weather_warning_te=weather_warning
        or "స్థానం ఇచ్చినట్లయితే పిచికారీకి ముందు వాతావరణ సూచనను తనిఖీ చేయండి.",
        confidence=0.35,
        source_notes=notes,
        image_received=image_received,
    )


def _lookup_weather_context(location: str | None) -> dict[str, str | None]:
    if not location or not location.strip():
        return {"summary": None, "warning": None}

    try:
        geo_response = requests.get(
            GEO_URL,
            params={
                "name": location.strip(),
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=8,
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        results = geo_data.get("results") or []
        if not results:
            return {"summary": None, "warning": None}

        place = results[0]
        latitude = place.get("latitude")
        longitude = place.get("longitude")
        resolved_name = ", ".join(
            part for part in [place.get("name"), place.get("admin1"), place.get("country")] if part
        )

        forecast_response = requests.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,wind_speed_10m,precipitation",
                "forecast_days": 1,
                "timezone": "auto",
            },
            timeout=8,
        )
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        current = forecast_data.get("current", {})
        temperature = current.get("temperature_2m")
        wind_speed = current.get("wind_speed_10m")
        precipitation = current.get("precipitation")

        summary = (
            f"Location resolved as {resolved_name}. "
            f"Current weather: {temperature}°C, wind {wind_speed} km/h, precipitation {precipitation} mm."
        )

        warning = None
        if precipitation is not None and float(precipitation) > 0:
            warning = "Rain is present or expected soon; avoid spraying until conditions improve."
        elif wind_speed is not None and float(wind_speed) >= 20:
            warning = "Wind is strong; spraying may drift and should be delayed."

        return {"summary": summary, "warning": warning}
    except Exception:
        return {"summary": None, "warning": None}


def _execute_weather_call(location: str) -> str:
    """Called when Gemma invokes the get_weather tool."""
    result = _lookup_weather_context(location)
    parts: list[str] = []
    if result.get("summary"):
        parts.append(result["summary"])
    if result.get("warning"):
        parts.append(f"Advisory: {result['warning']}")
    return " ".join(parts) if parts else "Weather data unavailable for this location."


def _load_json_from_text(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract JSON object from surrounding prose
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        return json.loads(text[start:end])
    raise json.JSONDecodeError("No JSON object found in model response", text, 0)


def _build_prompt(request: DiagnoseRequest, knowledge_context: str) -> str:
    location = request.location.strip() if request.location else ""
    weather_instruction = (
        "- Call get_weather with the farmer's location before giving any spraying or irrigation advice."
        if location
        else "- No location was provided; skip weather advice."
    )
    kb_section = (
        f"\n\nKnowledge base context (use this as a primary reference):\n{knowledge_context}"
        if knowledge_context
        else ""
    )
    return f"""You are Krishi Mitra, an expert agricultural assistant for Indian farmers.

Analyze the crop problem below and return ONLY a valid JSON object with these exact keys:
- summary_en: string (clear diagnosis in English)
- summary_te: string (same diagnosis in Telugu)
- likely_issue: string (disease, pest, or condition name)
- action_steps_en: array of 3-5 practical action strings in English
- action_steps_te: array of matching action strings in Telugu
- weather_warning_en: string or null
- weather_warning_te: string or null
- confidence: number 0.0 to 1.0
- source_notes: array of brief strings describing your reasoning sources

Rules:
- Output ONLY the JSON object. No markdown fences, no text outside the JSON.
- Use simple English and clear Telugu.
- If uncertain, state it plainly and set confidence below 0.5.
{weather_instruction}
- Use your search capability to supplement the knowledge base with current or regional information.{kb_section}

Farmer input:
- Crop: {request.crop_name.strip()}
- Problem: {request.problem_description.strip()}
- Location: {location or "not provided"}""".strip()


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
        logger.warning("GOOGLE_API_KEY not set — returning fallback diagnosis")
        weather = _lookup_weather_context(request.location)
        return _fallback_diagnosis(
            request,
            image_path is not None,
            weather_warning=weather["warning"],
            weather_summary=weather["summary"],
        )

    model = os.getenv("GEMMA_MODEL", DEFAULT_MODEL)
    logger.info("calling gemma model=%s image=%s", model, image_path is not None)
    client = genai.Client(api_key=api_key)

    kb_records = retrieve(request.crop_name, request.problem_description)
    knowledge_context = format_context(kb_records)
    logger.info("knowledge base matched %d record(s) for crop=%r", len(kb_records), request.crop_name)

    prompt = _build_prompt(request, knowledge_context)

    # Build initial contents
    contents: list[Any] = [prompt]
    if image_path is not None:
        uploaded = client.files.upload(
            file=str(image_path),
            config={"mimeType": image_content_type or "image/jpeg"},
        )
        contents = [uploaded, prompt]

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high"),
        system_instruction=(
            "You are a production agricultural assistant for Indian farmers. "
            "Return only a valid JSON object — no markdown fences, no text outside the JSON."
        ),
        tools=[
            types.Tool(function_declarations=[_WEATHER_FUNCTION]),
            {"google_search": {}},
        ],
    )

    response = client.models.generate_content(model=model, contents=contents, config=config)

    # Agentic loop: execute function calls until Gemma returns final text (max 3 turns)
    for turn in range(3):
        if not response.function_calls:
            break

        logger.info(
            "gemma requested %d function call(s) on turn %d",
            len(response.function_calls),
            turn + 1,
        )

        # Append the model's response turn to the conversation history
        contents = list(contents) + [response.candidates[0].content]

        # Execute each requested function and collect results
        fn_parts: list[types.Part] = []
        for fc in response.function_calls:
            if fc.name == "get_weather":
                location_arg = fc.args.get("location", request.location or "")
                result_text = _execute_weather_call(location_arg)
            else:
                result_text = f"Unknown function: {fc.name}"

            logger.info("function %s(%r) -> %.120s", fc.name, fc.args, result_text)
            fn_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={"result": result_text},
                    )
                )
            )

        contents = contents + [types.Content(role="user", parts=fn_parts)]
        response = client.models.generate_content(model=model, contents=contents, config=config)

    if not response.text:
        logger.warning("gemma returned empty text after %d turn(s)", turn + 1)
        weather = _lookup_weather_context(request.location)
        return _fallback_diagnosis(
            request,
            image_path is not None,
            weather_warning=weather["warning"],
            weather_summary=weather["summary"],
        )

    try:
        parsed = _load_json_from_text(response.text)
    except json.JSONDecodeError:
        logger.error("gemma response was not valid JSON: %.200s", response.text)
        weather = _lookup_weather_context(request.location)
        return _fallback_diagnosis(
            request,
            image_path is not None,
            weather_warning=weather["warning"],
            weather_summary=weather["summary"],
        )

    return _coerce_response(parsed, image_path is not None)


def generate_diagnosis(
    request: DiagnoseRequest,
    image_bytes: bytes | None,
    image_filename: str | None,
    image_content_type: str | None,
) -> DiagnoseResponse:
    crop = request.crop_name.strip()
    if not crop:
        weather = _lookup_weather_context(request.location)
        return _fallback_diagnosis(
            request,
            image_bytes is not None,
            weather_warning=weather["warning"],
            weather_summary=weather["summary"],
        )

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
        logger.exception("unhandled error in generate_diagnosis — returning fallback")
        weather = _lookup_weather_context(request.location)
        return _fallback_diagnosis(
            request,
            image_bytes is not None,
            weather_warning=weather["warning"],
            weather_summary=weather["summary"],
        )
    finally:
        if temp_file is not None:
            try:
                Path(temp_file.name).unlink(missing_ok=True)
            except OSError:
                pass
