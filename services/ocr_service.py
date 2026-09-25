"""
services/ocr_service.py
---------------------------
Extracts text from uploaded lab reports, prescriptions, or documents using
PyPDF2 (for PDFs) or Tesseract OCR (for images).
"""

import os
import PyPDF2
import pytesseract
from PIL import Image

from app.config import settings

if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


def extract_text(file_path: str) -> dict:
    """
    Extracts text from PDF or image file.
    Returns {"text": str, "confidence": float | None, "error": str | None}.
    """
    if not os.path.exists(file_path):
        return {"text": "", "confidence": None, "error": f"File not found: {file_path}"}

    ext = file_path.lower()

    # 1. PDF File Extraction via PyPDF2
    if ext.endswith(".pdf"):
        try:
            reader = PyPDF2.PdfReader(file_path)
            extracted_pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    extracted_pages.append(page_text.strip())
            
            combined_text = "\n".join(extracted_pages).strip()
            if combined_text:
                return {"text": combined_text, "confidence": 0.95, "error": None}
            else:
                return {
                    "text": "",
                    "confidence": None,
                    "error": "PDF uploaded, but no selectable text layer found."
                }
        except Exception as e:
            return {"text": "", "confidence": None, "error": f"PDF extraction error: {e}"}

    # 2. Image File Extraction (JPG, PNG, BMP, etc.) via Tesseract / PIL
    try:
        image = Image.open(file_path)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        words = [w for w in data.get("text", []) if w and w.strip()]
        confidences = [int(c) for c in data.get("conf", []) if str(c).isdigit() and int(c) >= 0]

        text = " ".join(words)
        avg_confidence = (sum(confidences) / len(confidences) / 100) if confidences else None

        return {"text": text, "confidence": avg_confidence, "error": None}
    except Exception as exc:
        return {
            "text": "",
            "confidence": None,
            "error": (
                f"OCR error: {exc}. The document is stored safely and can be reviewed manually."
            ),
        }
