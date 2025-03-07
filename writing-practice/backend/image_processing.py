# image_processing.py (added back)

import json
import logging
from PIL import Image
import streamlit as st
from .ocr_reader import load_ocr_reader
from claude_haiku import call_claude_haiku
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_and_grade_image(image_data, expected_text):
    """
    Process an image with OCR and grade it against expected text
    
    Args:
        image_data: Image data (bytes or file path)
        expected_text: Expected Chinese text
        
    Returns:
        Dictionary containing grading results
    """
    try:
        logger.debug("Starting image processing")
        logger.debug(f"Image data type: {type(image_data)}")
        logger.debug(f"Expected text: {expected_text}")
        
        # Convert image data to proper format
        try:
            if isinstance(image_data, bytes):
                logger.debug(f"Processing bytes of length: {len(image_data)}")
                img = Image.open(io.BytesIO(image_data))
            elif isinstance(image_data, Image.Image):
                logger.debug("Processing PIL Image directly")
                img = image_data
            else:
                logger.error(f"Unsupported image data type: {type(image_data)}")
                return {'error': 'Unsupported image format'}
            
            logger.debug(f"Image details - Format: {img.format}, Size: {img.size}, Mode: {img.mode}")
            
            # Convert image to RGB if needed
            if img.mode not in ['L', 'RGB']:
                logger.debug(f"Converting image from {img.mode} to RGB")
                img = img.convert('RGB')
            
            # Save to PNG format in memory
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            logger.debug(f"Converted image to PNG bytes: {len(img_byte_arr)} bytes")
            
        except Exception as e:
            logger.error(f"Error processing image data: {str(e)}", exc_info=True)
            return {'error': f'Image processing error: {str(e)}'}
        
        # Load OCR reader
        reader = load_ocr_reader()
        if not reader:
            logger.error("Failed to load OCR reader")
            return {'error': 'Failed to load OCR reader'}
        
        # Process the image with OCR
        logger.debug("Running OCR on image")
        try:
            results = reader.readtext(img_byte_arr)
            logger.debug(f"OCR results: {results}")
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}", exc_info=True)
            return {'error': f'OCR processing error: {str(e)}'}
        
        if not results:
            logger.warning("No text detected in image")
            return {
                'grade': 'F',
                'ocr_text': '',
                'error': 'No text detected in image'
            }
        
        # Extract and clean text from results
        try:
            detected_text = results[0][1]
            # Remove null bytes and clean whitespace
            detected_text = detected_text.replace('\x00', '').strip()
            logger.debug(f"Cleaned detected text: '{detected_text}'")
            logger.debug(f"Expected text: '{expected_text}'")
            
            # Calculate similarity
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, detected_text, expected_text).ratio()
            accuracy = round(similarity * 100, 2)
            logger.debug(f"Similarity score: {accuracy}%")
            
            # Assign grade based on accuracy
            if accuracy >= 90:
                grade = 'A'
            elif accuracy >= 80:
                grade = 'B'
            elif accuracy >= 70:
                grade = 'C'
            elif accuracy >= 60:
                grade = 'D'
            else:
                grade = 'F'
            
            return {
                'grade': grade,
                'accuracy': accuracy,
                'ocr_text': detected_text,
                'expected_text': expected_text,
                'similarity': similarity
            }
            
        except Exception as e:
            logger.error(f"Error processing OCR results: {str(e)}", exc_info=True)
            return {
                'grade': 'F',
                'error': f'Text processing error: {str(e)}',
                'ocr_text': '',
                'expected_text': expected_text
            }
            
    except Exception as e:
        logger.error(f"Error in grading: {str(e)}", exc_info=True)
        return {
            'grade': 'F',
            'error': str(e),
            'ocr_text': '',
            'expected_text': expected_text
        }