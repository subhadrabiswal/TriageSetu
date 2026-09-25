"""
services/stt_service.py
---------------------------
Speech-to-text happens in the browser via the Web Speech API
(see frontend/src/components/patient-intake/VoiceInput.jsx) so no
server round-trip or model hosting is needed for the demo - the
browser sends already-transcribed text to the normal symptom-intake
endpoint.

This file is a placeholder for a future server-side upgrade (e.g. a
hosted Whisper endpoint) for facilities whose devices don't support
in-browser speech recognition.
"""


def transcribe(audio_file_path: str) -> dict:
    return {
        "text": "",
        "error": "Server-side transcription is not configured. Use in-browser voice input instead.",
    }
