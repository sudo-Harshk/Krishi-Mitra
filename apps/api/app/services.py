from .schemas import DiagnoseRequest, DiagnoseResponse


def generate_template_diagnosis(
    request: DiagnoseRequest,
    image_received: bool,
) -> DiagnoseResponse:
    crop = request.crop_name.strip()
    issue = request.problem_description.strip()

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
        image_received=image_received,
    )

