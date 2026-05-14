import logging
import os

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .schemas import DiagnoseRequest, DiagnoseResponse
from .services import generate_diagnosis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
_allow_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Krishi Mitra API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/diagnose", response_model=DiagnoseResponse)
@limiter.limit("10/minute")
async def diagnose(
    request: Request,
    crop_name: str = Form(min_length=1),
    problem_description: str = Form(min_length=1),
    location: str | None = Form(default=None),
    image_file: UploadFile | None = File(default=None),
) -> DiagnoseResponse:
    logger.info(
        "diagnose request crop=%r location=%r image=%s",
        crop_name,
        location,
        image_file is not None,
    )

    payload = DiagnoseRequest(
        crop_name=crop_name,
        problem_description=problem_description,
        location=location,
    )

    if image_file is not None:
        if image_file.content_type is None or not image_file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="image_file must be an image")
        image_bytes = await image_file.read()
        await image_file.close()
    else:
        image_bytes = None

    result = generate_diagnosis(
        payload,
        image_bytes=image_bytes,
        image_filename=image_file.filename if image_file is not None else None,
        image_content_type=image_file.content_type if image_file is not None else None,
    )
    logger.info("diagnose response confidence=%.2f fallback=%s", result.confidence, result.confidence < 0.4)
    return result
