from app.config import get_settings
from app.services.ai_service import AIServiceError, AIServiceNotConfiguredError


def transcribe_burmese_audio(audio_bytes: bytes) -> str:
    """Transcribe a short Burmese audio file through Google Speech-to-Text V2."""
    settings = get_settings()
    if not settings.google_cloud_project:
        raise AIServiceNotConfiguredError("GOOGLE_CLOUD_PROJECT is not configured.")

    try:
        from google.api_core.client_options import ClientOptions
        from google.cloud.speech_v2 import SpeechClient
        from google.cloud.speech_v2.types import cloud_speech

        client = SpeechClient(
            client_options=ClientOptions(
                api_endpoint=f"{settings.speech_region}-speech.googleapis.com"
            )
        )
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["my-MM"],
            model=settings.speech_model,
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
            ),
        )
        response = client.recognize(
            request=cloud_speech.RecognizeRequest(
                recognizer=(
                    f"projects/{settings.google_cloud_project}/"
                    f"locations/{settings.speech_region}/recognizers/_"
                ),
                config=config,
                content=audio_bytes,
            )
        )
    except Exception as error:
        raise AIServiceError("Google Speech-to-Text could not transcribe this audio.") from error

    transcript = " ".join(
        result.alternatives[0].transcript
        for result in response.results
        if result.alternatives
    ).strip()
    if not transcript:
        raise AIServiceError("No speech was detected in the audio.")
    return transcript
