from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(title="Krishi Mitra API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DiagnoseRequest(BaseModel):
    crop_name: str = Field(min_length=1)
    problem_description: str = Field(min_length=1)
    location: str | None = None


class DiagnoseResponse(BaseModel):
    summary_en: str
    summary_te: str
    likely_issue: str
    action_steps_en: list[str]
    action_steps_te: list[str]
    weather_warning_en: str | None = None
    weather_warning_te: str | None = None
    confidence: float
    source_notes: list[str]
    image_received: bool


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(
    crop_name: str = Form(min_length=1),
    problem_description: str = Form(min_length=1),
    location: str | None = Form(default=None),
    image_file: UploadFile | None = File(default=None),
) -> DiagnoseResponse:
    payload = DiagnoseRequest(
        crop_name=crop_name,
        problem_description=problem_description,
        location=location,
    )

    crop = payload.crop_name.strip()
    issue = payload.problem_description.strip()
    image_received = False

    if image_file is not None:
        if image_file.content_type is None or not image_file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="image_file must be an image")
        image_received = True
        await image_file.read()
        await image_file.close()

    return DiagnoseResponse(
        summary_en=f"Likely crop issue detected for {crop}.",
        summary_te=f"{crop} పంటకు సంభవించే సమస్యను గుర్తించాం.",
        likely_issue=issue,
        action_steps_en=[
            "Inspect leaves and stems closely.",
            "Remove visibly affected parts if safe.",
            "Follow label guidance before spraying anything."
        ],
        action_steps_te=[
            "ఆకులు మరియు కాండాన్ని దగ్గరగా పరిశీలించండి.",
            "సురక్షితం అయితే ప్రభావిత భాగాలను తొలగించండి.",
            "ఏదైనా పిచికారీ చేసే ముందు లేబుల్ సూచనలు పాటించండి."
        ],
        weather_warning_en="Check the forecast before spraying if location is provided.",
        weather_warning_te="స్థానం ఇచ్చినట్లయితే పిచికారీకి ముందు వాతావరణ సూచనను తనిఖీ చేయండి.",
        confidence=0.72,
        source_notes=[
            "Template backend response",
            "Multipart image upload accepted",
            "RAG and Gemma flow to be integrated next"
        ],
        image_received=image_received
    )
