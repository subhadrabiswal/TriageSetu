"""
services/translation_service.py
-----------------------------------
Translates patient input into English using the Bhashini API.
"""

import os
import requests
from app.config import settings

PIPELINE_CONFIG_URL = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"


def bhashini_translate(text: str, source_lang: str, target_lang: str = "en") -> str:
    if not text or not text.strip():
        return text

    lang_map = {
        "hi": "hi",
        "or": "or",
        "en": "en",
        "hindi": "hi",
        "odia": "or",
        "english": "en"
    }
    src_lang = lang_map.get(source_lang.lower(), source_lang)
    tgt_lang = lang_map.get(target_lang.lower(), target_lang)

    if src_lang == tgt_lang:
        return text

    user_id = os.getenv("BHASHINI_USER_ID", "") or getattr(settings, "BHASHINI_USER_ID", "")
    ulca_key = os.getenv("BHASHINI_ULCA_API_KEY", "") or getattr(settings, "BHASHINI_ULCA_API_KEY", "")
    inference_key = os.getenv("BHASHINI_INFERENCE_KEY", "") or getattr(settings, "BHASHINI_INFERENCE_KEY", "") or getattr(settings, "TRANSLATION_API_KEY", "")

    # Try pipeline config URL pattern if credentials exist
    if user_id and ulca_key:
        try:
            headers = {
                "Content-Type": "application/json",
                "userID": user_id,
                "ulcaApiKey": ulca_key,
            }
            payload = {
                "pipelineTasks": [{
                    "taskType": "translation",
                    "config": {"language": {"sourceLanguage": src_lang, "targetLanguage": tgt_lang}}
                }],
                "pipelineRequestConfig": {"pipelineId": "64392f96daac500b55c543cd"}
            }
            config_res = requests.post(PIPELINE_CONFIG_URL, json=payload, headers=headers, timeout=5)
            if config_res.status_code == 200:
                config = config_res.json()
                endpoint_info = config.get("pipelineInferenceAPIEndPoint", {})
                callback_url = endpoint_info.get("callbackUrl")
                api_key_info = endpoint_info.get("inferenceApiKey", {})
                header_name = api_key_info.get("name", "Authorization")
                header_value = api_key_info.get("value", inference_key)

                response_config = config.get("pipelineResponseConfig", [])
                service_id = None
                if response_config and "config" in response_config[0]:
                    for item in response_config[0]["config"]:
                        if "serviceId" in item:
                            service_id = item["serviceId"]
                            break

                if callback_url and service_id:
                    compute_payload = {
                        "pipelineTasks": [{
                            "taskType": "translation",
                            "config": {
                                "language": {"sourceLanguage": src_lang, "targetLanguage": tgt_lang},
                                "serviceId": service_id
                            }
                        }],
                        "inputData": {"input": [{"source": text.strip()}]}
                    }
                    compute_headers = {
                        "Content-Type": "application/json",
                        header_name: header_value
                    }
                    comp_res = requests.post(callback_url, json=compute_payload, headers=compute_headers, timeout=8)
                    if comp_res.status_code == 200:
                        out_data = comp_res.json()
                        translated = out_data["pipelineResponse"][0]["output"][0]["target"]
                        if translated and translated.strip():
                            return translated.strip()
        except Exception as e:
            print("Bhashini pipeline config error:", e)

    # Fallback to direct Dhruva API call
    if inference_key:
        try:
            dhruva_url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
            dhruva_headers = {
                "Authorization": inference_key,
                "Content-Type": "application/json"
            }
            dhruva_payload = {
                "pipelineTasks": [{
                    "taskType": "translation",
                    "config": {"language": {"sourceLanguage": src_lang, "targetLanguage": tgt_lang}}
                }],
                "inputData": {"input": [{"source": text.strip()}]}
            }
            dh_res = requests.post(dhruva_url, json=dhruva_payload, headers=dhruva_headers, timeout=8)
            if dh_res.status_code == 200:
                dh_data = dh_res.json()
                translated = dh_data["pipelineResponse"][0]["output"][0]["target"]
                if translated and translated.strip():
                    return translated.strip()
        except Exception as e:
            print("Bhashini Dhruva call error:", e)

    return text


def translate_text_bhashini(text: str, source_language: str = "hi", target_language: str = "en") -> str:
    return bhashini_translate(text, source_lang=source_language, target_lang=target_language)


def translate_to_english(text: str, source_language: str) -> dict:
    if source_language == "en" or not text.strip():
        return {"translated_text": text, "was_translated": False}

    translated = bhashini_translate(text, source_lang=source_language, target_lang="en")
    was_translated = (translated != text)

    return {
        "translated_text": translated,
        "was_translated": was_translated,
    }
