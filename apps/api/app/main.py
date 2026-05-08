from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from .schemas import DiagnoseRequest, DiagnoseResponse
from .services import generate_template_diagnosis


app = FastAPI(title="Krishi Mitra API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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

    return generate_template_diagnosis(payload, image_received=image_received)
