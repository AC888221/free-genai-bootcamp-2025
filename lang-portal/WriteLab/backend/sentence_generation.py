# sentence_generation.py

import json
import requests
from bedrock_client import BedrockClient
import sys
import os
import logging
import time
import traceback

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import streamlit as st
    use_streamlit = True
except ImportError:
    use_streamlit = False

class SentenceGenerator:
    def __init__(self):
        """Initialize Sentence Generator"""
        try:
            # Explicitly pass the model ID from config to ensure consistency
            logger.info(f"Initializing SentenceGenerator with model ID: {config.CLAUDE_MODEL_ID}")
            self.bedrock_client = BedrockClient(model_id=config.CLAUDE_MODEL_ID)
            
            if self.bedrock_client.get_client() is None:
                logger.warning("Failed to create Bedrock client. Using fallback mode.")
                self.fallback_mode = True
                if use_streamlit:
                    st.warning("⚠️ Failed to initialize Bedrock client. Using fallback mode with pre-defined sentences.")
            else:
                self.fallback_mode = False
        except Exception as e:
            logger.warning(f"Error initializing Bedrock client: {str(e)}")
            logger.warning(traceback.format_exc())
            self.fallback_mode = True
            self.bedrock_client = None
            if use_streamlit:
                st.warning("⚠️ Error initializing Bedrock client. Using fallback mode with pre-defined sentences.")

    def generate_sentence(self, _word):
        """
        Generate a simple sentence using the provided Chinese word.
        
        Args:
            _word (str): The Chinese word to be used in the sentence.
        
        Returns:
            dict: A dictionary containing the English sentence, Chinese sentence, and pinyin.
        """
        try:
            logger.info("Generating sentence for word: %s", _word)
            prompt = f"""
            Generate a simple sentence using the following Chinese word: {_word}
            The grammar should be scoped to HSK Level 1-2 grammar patterns.
            You can use the following vocabulary to construct a simple sentence:
            - Common objects (e.g., book/书, water/水, food/食物)
            - Basic verbs (e.g., to eat/吃, to drink/喝, to go/去)
            - Simple time expressions (e.g., today/今天, tomorrow/明天, yesterday/昨天)

            Return ONLY the following in JSON format:
            {{
              "english": "The English sentence",
              "chinese": "The Chinese sentence in simplified characters",
              "pinyin": "The pinyin representation with tone marks"
            }}
            """
            
            logger.info("Sending request to Bedrock API...")
            response_text = self.bedrock_client.generate_response(prompt, {"temperature": 0.3})
            
            if response_text is None:
                raise ValueError("Received no response from Bedrock API.")
            
            logger.info("Received response from Bedrock API.")
            response_text = response_text.strip()
            
            if response_text.find('{') >= 0 and response_text.rfind('}') >= 0:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                sentence_data = json.loads(json_str)
                
                logger.info("Successfully parsed response.")
                return sentence_data
            else:
                logger.warning("Response does not contain valid JSON. Returning default sentence.")
                return {
                    "english": "I want to learn Chinese",
                    "chinese": "我想学中文",
                    "pinyin": "wǒ xiǎng xué zhōngwén"
                }
                
        except Exception as e:
            logger.error(f"Error generating sentence: {str(e)}")
            if use_streamlit:
                st.error(f"Error generating sentence: {str(e)}")
            return {
                "error": str(e)
            }

    def translate_chinese(self, chinese_text):
        """Generate English translation and Pinyin for Chinese text."""
        try:
            logger.info("Translating Chinese text: %s", chinese_text)
            prompt = f"""
            Translate the following Chinese text and provide its pinyin:
            {chinese_text}

            Return ONLY the following in JSON format:
            {{
              "english": "The English translation",
              "chinese": "{chinese_text}",
              "pinyin": "The pinyin representation with tone marks"
            }}
            """
            
            response_text = self.bedrock_client.generate_response(prompt, {"temperature": 0.3})
            
            if response_text is None:
                raise ValueError("Received no response from Bedrock API.")
            
            response_text = response_text.strip()
            
            if response_text.find('{') >= 0 and response_text.rfind('}') >= 0:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("Response does not contain valid JSON")
                
        except Exception as e:
            logger.error(f"Error translating Chinese: {str(e)}")
            return {"error": str(e)}

    def translate_english(self, english_text):
        """Generate Chinese translation and Pinyin for English text."""
        try:
            logger.info("Translating English text: %s", english_text)
            prompt = f"""
            Translate the following English text to Chinese and provide its pinyin:
            {english_text}

            Return ONLY the following in JSON format:
            {{
              "english": "{english_text}",
              "chinese": "The Chinese translation in simplified characters",
              "pinyin": "The pinyin representation with tone marks"
            }}
            """
            
            response_text = self.bedrock_client.generate_response(prompt, {"temperature": 0.3})
            
            if response_text is None:
                raise ValueError("Received no response from Bedrock API.")
            
            response_text = response_text.strip()
            
            if response_text.find('{') >= 0 and response_text.rfind('}') >= 0:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("Response does not contain valid JSON")
                
        except Exception as e:
            logger.error(f"Error translating English: {str(e)}")
            return {"error": str(e)}

    def store_sentence(self, api_url, group_id, sentence_data):
        """
        Store the generated sentence in the lang-portal app.
        
        Args:
            api_url (str): The API URL for storing the sentence.
            group_id (int): The group ID for storing the sentence.
            sentence_data (dict): The sentence data to be stored.
        """
        try:
            logger.info("Storing sentence to API: %s", api_url)
            response = requests.post(f"{api_url}/groups/{group_id}/sentences", json=sentence_data)
            if response.status_code != 201:
                logger.warning("Failed to store the generated sentence. Status code: %d", response.status_code)
                if use_streamlit:
                    st.warning("Failed to store the generated sentence in the lang-portal app. The app will continue to function with read-only access.")
            else:
                logger.info("Successfully stored the sentence.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with the lang-portal app: {e}")
            if use_streamlit:
                st.warning(f"Error communicating with the lang-portal app: {e}. The app will continue to function with read-only access.")

if __name__ == "__main__":
    sentence_generator = SentenceGenerator()
    chinese_word = input("Enter the Chinese word: ")
    
    result = sentence_generator.generate_sentence(chinese_word)
    if "error" in result:
        logger.error(f"Error generating sentence: {result['error']}")
        print(f"Error generating sentence: {result['error']}")
    else:
        print("Generated Sentence:")
        print(f"English: {result['english']}")
        print(f"Chinese: {result['chinese']}")
        print(f"Pinyin: {result['pinyin']}")
        
        # Ask user if they want to store the sentence
        store = input("Do you want to store this sentence? (yes/no): ").strip().lower()
        if store == 'yes':
            group_id = int(input("Enter the group ID: "))
            try:
                sentence_generator.store_sentence(config.API_URL, group_id, result)
                print("Sentence stored successfully.")
            except Exception as e:
                logger.error(f"Error storing sentence: {e}")
                print(f"Error storing sentence: {e}")