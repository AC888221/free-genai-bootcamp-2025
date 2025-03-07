# ocr_reader.py (added back)

import pytesseract
from PIL import Image
import logging
import io
import sys

# Configure logging with more detail and output to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ocr_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PyTesseractReader:
    """A wrapper class to make pytesseract compatible with the EasyOCR-like interface"""
    
    def __init__(self):
        self.lang = 'chi_sim'  # Default to Simplified Chinese
        logger.info("Initializing PyTesseractReader with language: chi_sim")
    
    def readtext(self, image_data):
        """
        Read text from image data, mimicking EasyOCR's readtext method
        
        Args:
            image_data: Can be a file path, PIL Image, or image bytes
            
        Returns:
            A list of tuples in format: [(bounding_box, text, confidence)]
        """
        try:
            logger.debug(f"Received image data of type: {type(image_data)}")
            
            # Handle different input types
            if isinstance(image_data, str):  # File path
                logger.debug(f"Processing file path: {image_data}")
                img = Image.open(image_data)
            elif isinstance(image_data, Image.Image):  # PIL Image
                logger.debug("Processing PIL Image object")
                img = image_data
            elif isinstance(image_data, bytes):  # Image bytes
                logger.debug(f"Processing image bytes of length: {len(image_data)}")
                try:
                    # Create a new BytesIO object and write the bytes to it
                    byte_stream = io.BytesIO(image_data)
                    byte_stream.seek(0)  # Reset the stream position
                    img = Image.open(byte_stream)
                    logger.debug("Successfully opened image from bytes")
                except Exception as e:
                    logger.error(f"Error opening image from bytes: {str(e)}")
                    # Try to decode the image using PIL's raw decoder
                    try:
                        img = Image.frombytes('RGB', (1, 1), image_data)
                        logger.debug("Successfully decoded image using frombytes")
                    except Exception as e2:
                        logger.error(f"Error decoding image: {str(e2)}")
                        return []
            else:
                logger.error(f"Unsupported image data type: {type(image_data)}")
                return []
            
            # Log image details
            logger.debug(f"Image size: {img.size}, Mode: {img.mode}, Format: {img.format}")
            
            # Ensure image is in a format Tesseract can handle
            if img.format not in ['PNG', 'JPEG', 'BMP', 'TIFF']:
                logger.debug(f"Converting image format from {img.format} to PNG")
                # Convert to RGB if needed
                if img.mode not in ['RGB', 'L']:
                    img = img.convert('RGB')
                # Save to PNG format in memory
                png_buffer = io.BytesIO()
                img.save(png_buffer, format='PNG')
                png_buffer.seek(0)
                img = Image.open(png_buffer)
            
            # Convert to grayscale if needed
            if img.mode != 'L':
                logger.debug(f"Converting image from {img.mode} to grayscale")
                img = img.convert('L')
            
            # Use pytesseract to get text
            logger.debug("Starting OCR processing with pytesseract")
            try:
                # Get detailed OCR data
                ocr_data = pytesseract.image_to_data(img, lang=self.lang, output_type=pytesseract.Output.DICT)
                logger.debug(f"OCR Data keys: {ocr_data.keys()}")
                logger.debug(f"Confidence scores: {ocr_data.get('conf', [])}")
                
                # Get the text
                text = pytesseract.image_to_string(img, lang=self.lang)
                logger.debug(f"Raw OCR text output: '{text}'")
                
                # Clean the text - remove null bytes and extra whitespace
                text = text.replace('\x00', '').strip()
                logger.debug(f"Cleaned OCR text output: '{text}'")
                
                # If text is found, return in a format similar to EasyOCR
                if text:
                    # Create a dummy bounding box (0,0,width,height)
                    width, height = img.size
                    bbox = ((0, 0), (width, 0), (width, height), (0, height))
                    
                    result = [(bbox, text, 0.9)]  # Using fixed confidence of 0.9
                    logger.info(f"Successfully extracted text: {text}")
                    return result
                else:
                    logger.warning("No text detected in image")
                    return []
                    
            except pytesseract.TesseractError as te:
                logger.error(f"Tesseract error: {te}")
                return []
                
        except Exception as e:
            logger.error(f"Error in readtext: {str(e)}", exc_info=True)
            return []

def load_ocr_reader():
    """
    Load and return a PyTesseractReader instance that mimics EasyOCR interface
    """
    try:
        logger.info("Creating new PyTesseractReader instance")
        reader = PyTesseractReader()
        return reader
    except Exception as e:
        logger.error(f"Error loading OCR reader: {str(e)}", exc_info=True)
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
        logger.debug(f"Processing image at path: {image_path}")
        img = Image.open(image_path)
        logger.debug(f"Image opened successfully. Size: {img.size}, Mode: {img.mode}")
        text = pytesseract.image_to_string(img, lang='chi_sim')
        logger.info(f"OCR result: '{text}'")
        return text
    except Exception as e:
        logger.error(f"Error processing image for OCR: {str(e)}", exc_info=True)
        return "Error processing image"