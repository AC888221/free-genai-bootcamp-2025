# sentence_generation.py (added back)

import config
import json
import requests
import streamlit as st
from claude_haiku import call_claude_haiku

@st.experimental_memo(ttl=60)
def generate_sentence(api_url, group_id, _word):
    try:
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
        
        response = call_claude_haiku(prompt, temperature=0.3)
        
        response = response.strip()
        
        if response.find('{') >= 0 and response.rfind('}') >= 0:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            sentence_data = json.loads(json_str)
            
            store_sentence(api_url, group_id, sentence_data)
            
            return sentence_data
        else:
            return {
                "english": "I want to learn Chinese",
                "chinese": "我想学中文",
                "pinyin": "wǒ xiǎng xué zhōngwén"
            }
            
    except Exception as e:
        st.error(f"Error generating sentence: {str(e)}")
        return {
            "english": "I want to learn Chinese",
            "chinese": "我想学中文",
            "pinyin": "wǒ xiǎng xué zhōngwén"
        }

def store_sentence(api_url, group_id, sentence_data):
    try:
        response = requests.post(f"{api_url}/groups/{group_id}/sentences", json=sentence_data)
        if response.status_code != 201:
            st.warning("Failed to store the generated sentence in the lang-portal app. The app will continue to function with read-only access.")
    except requests.exceptions.RequestException as e:
        st.warning(f"Error communicating with the lang-portal app: {e}. The app will continue to function with read-only access.")