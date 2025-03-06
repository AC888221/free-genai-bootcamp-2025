# ocr_reader.py (added back)

import pytesseract
from PIL import Image
import logging
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PyTesseractReader:
    """A wrapper class to make pytesseract compatible with the EasyOCR-like interface"""
    
    def __init__(self):
        self.lang = 'chi_sim'  # Default to Simplified Chinese
    
    def readtext(self, image_data):
        """
        Read text from image data, mimicking EasyOCR's readtext method
        
        Args:
            image_data: Can be a file path, PIL Image, or image bytes
            
        Returns:
            A list of tuples in format: [(bounding_box, text, confidence)]
        """
        try:
            # Handle different input types
            if isinstance(image_data, str):  # File path
                img = Image.open(image_data)
            elif isinstance(image_data, Image.Image):  # PIL Image
                img = image_data
            elif isinstance(image_data, bytes):  # Image bytes
                img = Image.open(io.BytesIO(image_data))
            else:
                logger.error(f"Unsupported image data type: {type(image_data)}")
                return []
            
            # Convert to grayscale if needed
            if img.mode != 'L':
                img = img.convert('L')
            
            # Use pytesseract to get text
            text = pytesseract.image_to_string(img, lang=self.lang)
            
            # If text is found, return in a format similar to EasyOCR
            if text.strip():
                # Create a dummy bounding box (0,0,width,height)
                width, height = img.size
                bbox = ((0, 0), (width, 0), (width, height), (0, height))
                
                # Return in format similar to EasyOCR: [(bbox, text, confidence)]
                return [(bbox, text.strip(), 0.9)]  # Using fixed confidence of 0.9
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error in readtext: {e}")
            return []

def load_ocr_reader():
    """
    Load and return a PyTesseractReader instance that mimics EasyOCR interface
    """
    try:
        reader = PyTesseractReader()
        return reader
    except Exception as e:
        logger.error(f"Error loading OCR reader: {e}")
        return None

def ocr_image(image_path):
    """
    Process an image with OCR and return the extracted text
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text as a string
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='chi_sim')  # 'chi_sim' for Simplified Chinese
        return text
    except Exception as e:
        logger.error(f"Error processing image for OCR: {e}")
        return "Error processing image"