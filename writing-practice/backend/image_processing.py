# image_processing.py (added back)

import json
import logging
from PIL import Image
import streamlit as st
from ocr_reader import load_ocr_reader
from claude_haiku import call_claude_haiku

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

reader = load_ocr_reader()

def process_and_grade_image(image, expected_chinese):
    try:
        # If image is a file path or file-like object, open it
        if not isinstance(image, Image.Image):
            img = Image.open(image).convert('L')
        else:
            img = image.convert('L')
            
        img_array = img.tobytes()
        
        results = reader.readtext(img_array)
        
        transcribed_text = " ".join([res[1] for res in results]) if results else "No text detected"
        
        # Get the English sentence from session state if available
        english_sentence = ""
        if 'current_sentence' in st.session_state and 'english' in st.session_state['current_sentence']:
            english_sentence = st.session_state['current_sentence']['english']
        
        prompt = f"""
        I am analyzing a student's handwritten Chinese characters.

        Original English sentence: {english_sentence}
        Expected Chinese characters: {expected_chinese}
        OCR transcription of student's writing: {transcribed_text}

        Task 1: First, provide a literal English translation of the transcribed Chinese text.
        
        Task 2: Grade the student's writing based on how well it matches the expected Chinese characters.
        Use the S-A-B-C-D grading scale where:
        - S: Perfect match
        - A: Very good (>80% accuracy)
        - B: Good (>60% accuracy)
        - C: Needs improvement (>40% accuracy)
        - D: Significant errors (<40% accuracy)
        
        Task 3: Provide specific feedback on the characters and suggestions for improvement.

        Format your response as JSON:
        {{
          "back_translation": "English translation of transcribed text",
          "grade": "Grade letter (S/A/B/C/D)",
          "accuracy": decimal between 0-1,
          "feedback": "Specific feedback with suggestions"
        }}
        """
        
        response = call_claude_haiku(prompt, temperature=0.1)
        
        if response is None:
            raise ValueError("Received no response from Claude Haiku API.")
        
        response = response.strip()
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        json_str = response[start_idx:end_idx]
        grading_result = json.loads(json_str)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        grading_result = {
            "back_translation": "Translation unavailable",
            "grade": "C",
            "accuracy": 0.5,
            "feedback": "Some characters were recognized but there are errors. Keep practicing!"
        }
    except Exception as e:
        logger.error(f"Error in grading: {e}")
        grading_result = {
            "back_translation": "No text detected" if 'transcribed_text' in locals() and transcribed_text == "No text detected" else "Translation unavailable",
            "grade": "D" if 'transcribed_text' in locals() and transcribed_text == "No text detected" else "C",
            "accuracy": 0 if 'transcribed_text' in locals() and transcribed_text == "No text detected" else 0.5,
            "feedback": "No Chinese characters were detected in the image. Please try again with clearer handwriting." if 'transcribed_text' in locals() and transcribed_text == "No text detected" else "Some characters were recognized but there are errors. Keep practicing!"
        }
    
    # Initialize transcribed_text if it wasn't set in the try block
    if 'transcribed_text' not in locals():
        transcribed_text = "No text detected"
    
    char_comparison = []
    for i, expected_char in enumerate(expected_chinese):
        if i < len(transcribed_text):
            is_correct = expected_char == transcribed_text[i]
            char_comparison.append({
                "expected": expected_char,
                "written": transcribed_text[i],
                "correct": is_correct
            })
        else:
            char_comparison.append({
                "expected": expected_char,
                "written": "",
                "correct": False
            })
    
    for i in range(len(expected_chinese), len(transcribed_text)):
        char_comparison.append({
            "expected": "",
            "written": transcribed_text[i],
            "correct": False
        })
    
    result = {
        "transcription": transcribed_text,
        "back_translation": grading_result.get("back_translation", "Translation unavailable"),
        "accuracy": grading_result.get("accuracy", 0.5),
        "grade": grading_result.get("grade", "C"),
        "feedback": grading_result.get("feedback", "Keep practicing!"),
        "char_comparison": char_comparison
    }
    
    return result