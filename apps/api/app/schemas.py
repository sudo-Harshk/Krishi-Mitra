from pydantic import BaseModel, Field


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

