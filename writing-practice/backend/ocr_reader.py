# ocr_reader.py (added back)

import pytesseract
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_ocr_reader():
    return pytesseract

def ocr_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='chi_sim')  # 'chi_sim' for Simplified Chinese
        return text
    except Exception as e:
        logger.error(f"Error processing image for OCR: {e}")
        return "Error processing image"