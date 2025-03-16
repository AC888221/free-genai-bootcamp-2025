import streamlit as st
import requests
import base64
import io
from typing import Optional, Dict, Any, Tuple
import os
import logging
import sys
import time
import json
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/megatalk.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
MEGASERVICE_URL = os.getenv("MEGASERVICE_URL", "http://localhost:9500")
BASE_TIMEOUT = 300  # Base timeout in seconds
TIMEOUT_PER_CHAR = 1  # Additional timeout per character in seconds

# Constants
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="OPEA MegaTalk",
    page_icon="🤖",
    layout="wide",
)

# Title and description
st.title("🤖 OPEA MegaTalk")
st.markdown("### Your Language Buddy with Voice Response")

# Initialize session state for service status tracking
if "service_status" not in st.session_state:
    st.session_state.service_status = {
        "llm_service": {"status": "unknown", "last_check": None},
        "tts_service": {"status": "unknown", "last_check": None},
        "megaservice": {"status": "unknown", "last_check": None}
    }

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Add HSK level selector first
    hsk_level = st.selectbox(
        "Chinese Language Level",
        ["HSK 1 (Beginner)", "HSK 2 (Elementary)", "HSK 3 (Intermediate)", 
         "HSK 4 (Advanced Intermediate)", "HSK 5 (Advanced)", "HSK 6 (Mastery)"],
        index=0,  # Default to HSK 1
        help="Select the HSK level for Chinese responses"
    )
    
    # Then add other configuration options
    model = st.selectbox(
        "LLM Model",
        ["Qwen/Qwen2.5-0.5B-Instruct", "other-model-1", "other-model-2"],
        index=0
    )
    
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher values make output more random, lower values more deterministic"
    )
    
    max_tokens = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=2000,
        value=1000,
        step=100,
        help="Maximum number of tokens to generate"
    )
    
    voice = st.selectbox(
        "Voice",
        ["default", "voice1", "voice2"],
        index=0
    )
    
    generate_audio = st.checkbox("Generate Audio", value=True)
    
    # Add service status section
    st.header("Service Status")
    if st.button("Check Services"):
        with st.spinner("Checking services..."):
            try:
                # Check megaservice
                mega_response = requests.get(f"{MEGASERVICE_URL}/health", timeout=5)
                st.session_state.service_status["megaservice"] = {
                    "status": "online" if mega_response.status_code == 200 else "error",
                    "last_check": time.time(),
                    "details": mega_response.json() if mega_response.status_code == 200 else {"error": str(mega_response.status_code)}
                }
                
                # Check TTS info
                tts_response = requests.get(f"{MEGASERVICE_URL}/debug/tts-info", timeout=10)
                if tts_response.status_code == 200:
                    tts_data = tts_response.json()
                    working_endpoints = [ep for ep, info in tts_data.get("endpoints", {}).items() 
                                        if info.get("post_status", {}).get("result") == "WORKING"]
                    
                    st.session_state.service_status["tts_service"] = {
                        "status": "online" if working_endpoints else "error",
                        "last_check": time.time(),
                        "working_endpoints": working_endpoints,
                        "details": tts_data
                    }
                else:
                    st.session_state.service_status["tts_service"] = {
                        "status": "error",
                        "last_check": time.time(),
                        "details": {"error": f"Status {tts_response.status_code}"}
                    }
                    
            except Exception as e:
                for service in ["megaservice", "tts_service"]:
                    if st.session_state.service_status[service]["status"] == "unknown":
                        st.session_state.service_status[service] = {
                            "status": "error",
                            "last_check": time.time(),
                            "details": {"error": str(e)}
                        }
    
    # Display service status
    for service, info in st.session_state.service_status.items():
        status = info["status"]
        color = "green" if status == "online" else "red" if status == "error" else "gray"
        last_check = info.get("last_check")
        last_check_str = time.strftime("%H:%M:%S", time.localtime(last_check)) if last_check else "Never"
        
        st.markdown(f"**{service}**: <span style='color:{color}'>{status}</span> (Last check: {last_check_str})", unsafe_allow_html=True)
        
        if service == "tts_service" and status == "online":
            working_endpoints = info.get("working_endpoints", [])
            if working_endpoints:
                st.markdown(f"Working endpoints: {', '.join(working_endpoints)}")

# Main content area
user_input = st.text_area("Enter your message:", height=150)

# Add startup logging
logger.info("Starting MegaTalk application")
logger.info(f"MEGASERVICE_URL: {MEGASERVICE_URL}")

def calculate_timeout(input_text):
    """Calculate timeout based on input text length."""
    return BASE_TIMEOUT + (len(input_text) * TIMEOUT_PER_CHAR)

def get_hsk_prompt(hsk_level: str) -> str:
    """Get the appropriate system prompt for the selected HSK level."""
    hsk_prompts = {
        "HSK 1 (Beginner)": """Language Rules:
1. Only use HSK 1 vocabulary (150 basic words)
2. Use simple greetings: 你好, 再见
3. Basic pronouns: 我, 你, 他
4. Simple verbs: 是, 有, 喜欢
5. Keep sentences under 5 words
Example: 你好！我是老师。""",
        
        "HSK 2 (Elementary)": """Language Rules:
1. Use HSK 1-2 vocabulary (300 words)
2. Simple time expressions: 今天, 明天
3. Basic questions: 什么, 谁, 哪里
4. Common actions: 吃, 喝, 说, 看
5. Keep sentences under 8 words
Example: 今天天气很好，我很高兴。""",
        
        "HSK 3 (Intermediate)": """Language Rules:
1. Use HSK 1-3 vocabulary (600 words)
2. Express opinions: 我觉得, 我认为
3. Time and sequence: 以前, 然后, 最后
4. Compare things: 比, 更, 最
5. Keep sentences under 10 words
Example: 我觉得学习中文很有意思。""",
        
        "HSK 4 (Advanced Intermediate)": """Language Rules:
1. Use HSK 1-4 vocabulary (1200 words)
2. Complex emotions: 激动, 失望, 担心
3. Abstract concepts: 经验, 机会, 建议
4. Use 因为...所以... structures
5. Keep sentences under 15 words
Example: 因为你说得很好，所以我很佩服你。""",
        
        "HSK 5 (Advanced)": """Language Rules:
1. Use HSK 1-5 vocabulary (2500 words)
2. Professional terms: 研究, 调查, 分析
3. Complex opinions: 据我所知, 在我看来
4. Use idioms carefully: 马马虎虎, 半途而废
5. Keep sentences under 20 words
Example: 在我看来，学习语言需要持之以恒。""",
        
        "HSK 6 (Mastery)": """Language Rules:
1. Use full HSK vocabulary (5000+ words)
2. Academic language: 理论, 观点, 假设
3. Literary expressions: 引经据典
4. Complex structures: 不但...而且..., 即使...也...
5. Keep sentences under 25 words
Example: 掌握一门语言不仅需要勤奋，而且要有正确的学习方法。"""
    }
    return hsk_prompts.get(hsk_level, hsk_prompts["HSK 1 (Beginner)"])

def save_audio(audio_data: bytes, request_id: str) -> Path:
    """Save audio data to file and return the path."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"response_{timestamp}_{request_id[:8]}.wav"
    audio_path = AUDIO_DIR / filename
    
    with open(audio_path, "wb") as f:
        f.write(audio_data)
    
    return audio_path

def call_megaservice(text: str, params: Dict[str, Any]) -> Tuple[Optional[str], Optional[bytes], Optional[str], Dict[str, Any]]:
    """
    Call the megaservice with error handling and retries.
    Returns: (text_response, audio_data, error_message, details)
    """
    start_time = time.time()
    request_id = f"frontend_{int(start_time)}_{hash(text)}"
    details = {"request_id": request_id, "timestamp": start_time}
    
    # Base system prompt
    system_prompt = """You are a friendly AI Putonghua buddy. Please answer all questions in Putonghua. Even if the user asks in English, please answer in Putonghua. Keep your answers friendly, and natural.
    
    Rules:
    1. ALWAYS respond in Chinese (no English)
    2. Keep responses short (under 30 characters)
    3. Use natural, conversational tone
    4. One short sentence is best
    """
    
    # Add HSK level-specific instructions
    hsk_prompt = get_hsk_prompt(params.get("hsk_level", "HSK 1 (Beginner)"))
    full_system_prompt = f"{system_prompt}\n\n{hsk_prompt}"
    
    # Concatenate system prompt with user input
    full_prompt = f"{full_system_prompt}\n\nUser: {text}\nAssistant:"
    
    try:
        logger.info(f"[{request_id}] Sending request to megaservice")
        
        with st.spinner("Processing request..."):
            response = requests.post(
                f"{MEGASERVICE_URL}/v1/megaservice",
                json={
                    "text": full_prompt,  # Use the concatenated prompt
                    "model": params.get("model", "Qwen/Qwen2.5-0.5B-Instruct"),
                    "temperature": params.get("temperature", 0.7),
                    "max_tokens": params.get("max_tokens", 1000),
                },
                timeout=calculate_timeout(text)
            )
            
            details["response_time"] = time.time() - start_time
            details["status_code"] = response.status_code
            
            if response.status_code != 200:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(response.content))
                    details["error_data"] = error_data
                except:
                    error_detail = str(response.content)
                
                logger.error(f"[{request_id}] Service error: {error_detail}")
                return None, None, f"Service error ({response.status_code}): {error_detail}", details
            
            data = response.json()
            text_response = data.get("text_response")
            details["response_length"] = len(text_response) if text_response else 0
            
            # If audio is requested, make a separate call to GPT-SoVITS
            audio_data = None
            audio_path = None
            if params.get("generate_audio", True):
                try:
                    logger.info(f"[{request_id}] Requesting audio from GPT-SoVITS for text: {text_response[:100]}...")
                    tts_response = requests.post(
                        "http://gpt-sovits-service:9880/v1/audio/speech",
                        json={"input": text_response},
                        timeout=30
                    )
                    
                    if tts_response.status_code == 200:
                        audio_data = tts_response.content
                        # Save the audio file
                        audio_path = save_audio(audio_data, request_id)
                        details["audio_path"] = str(audio_path)
                        details["audio_size"] = len(audio_data)
                        logger.info(f"[{request_id}] Successfully saved audio to {audio_path}")
                    else:
                        error_msg = f"TTS request failed: {tts_response.status_code}: {tts_response.text}"
                        details["tts_error"] = error_msg
                        logger.warning(f"[{request_id}] {error_msg}")
                        
                except Exception as e:
                    error_msg = f"TTS request failed: {str(e)}"
                    details["tts_error"] = error_msg
                    logger.error(f"[{request_id}] {error_msg}")
            
            logger.info(f"[{request_id}] Request completed successfully in {details['response_time']:.2f}s")
            
            # Add to chat history with audio path
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            chat_entry = {
                "timestamp": time.time(),
                "request_id": request_id,
                "user_input": text,
                "response": text_response,
                "audio_path": str(audio_path) if audio_path else None,
                "details": details
            }
            st.session_state.chat_history.append(chat_entry)
            
            return text_response, audio_data, None, details
            
    except requests.exceptions.Timeout:
        logger.error(f"[{request_id}] Request timed out after {time.time() - start_time:.2f}s")
        details["error_type"] = "timeout"
        return None, None, f"Request timed out after {int(time.time() - start_time)}s. The service might be busy.", details
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[{request_id}] Connection error: {str(e)}")
        details["error_type"] = "connection"
        details["error"] = str(e)
        return None, None, "Could not connect to the service. Please check if it's running.", details
    except Exception as e:
        logger.exception(f"[{request_id}] Unexpected error")
        details["error_type"] = "unexpected"
        details["error"] = str(e)
        details["traceback"] = traceback.format_exc()
        return None, None, f"Error: {str(e)}", details

def fetch_audio_files():
    """Fetch list of audio files from the API"""
    try:
        response = requests.get(f"{MEGASERVICE_URL}/v1/audio/files")
        if response.status_code == 200:
            return response.json()["files"]
        else:
            logger.error(f"Failed to fetch audio files: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching audio files: {str(e)}")
        return []

def download_audio_file(filename):
    """Download an audio file from the API"""
    try:
        response = requests.get(f"{MEGASERVICE_URL}/audio/{filename}")
        if response.status_code == 200:
            local_path = AUDIO_DIR / filename
            local_path.write_bytes(response.content)
            return local_path
        else:
            logger.error(f"Failed to download audio file: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading audio file: {str(e)}")
        return None

def display_conversation():
    """Display the conversation history with audio playback"""
    if "chat_history" not in st.session_state:
        return

    for i, entry in enumerate(reversed(st.session_state.chat_history)):
        st.write(f"### Request {len(st.session_state.chat_history) - i}")
        st.write(f"Time: {time.strftime('%H:%M:%S', time.localtime(entry['timestamp']))}")
        
        # Display the text response
        st.write("**Response:**")
        st.write(entry["response"])
        
        # Handle audio playback
        if entry.get("audio_path"):
            try:
                audio_file = Path(entry["audio_path"])
                if audio_file.exists():
                    st.audio(str(audio_file), format="audio/wav")
                else:
                    st.warning(f"Audio file not found: {audio_file}")
            except Exception as e:
                st.error(f"Error playing audio: {str(e)}")
        else:
            st.info("No audio available for this response")
        
        st.divider()

if st.button("Submit"):
    if not user_input.strip():
        st.error("Please enter a message")
    else:
        try:
            request_params = {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "voice": voice,
                "generate_audio": generate_audio,
                "hsk_level": hsk_level
            }
            
            logger.info(f"Sending request to megaservice: {user_input[:100]}...")
            text_response, audio_data, error, details = call_megaservice(user_input, request_params)
            
            # Store request details
            if "request_history" not in st.session_state:
                st.session_state.request_history = []
            st.session_state.request_history.append(details)
            
            if error:
                st.error(error)
                
                # Add troubleshooting guidance for specific error types
                if "tts" in error.lower() or "audio" in error.lower():
                    st.warning("Audio generation failed. You might want to try again without audio generation or check the TTS service status.")
                elif "timeout" in error.lower():
                    st.warning("The request timed out. This might indicate the server is busy or the model is generating a very long response.")
                elif "connection" in error.lower():
                    st.warning("Connection error. Please verify the services are running and properly configured.")
            else:
                logger.info("Successfully received response from megaservice")
                
                # Display text response
                st.subheader("Text Response")
                st.write(text_response)
                
                # Display audio if available
                if generate_audio:
                    if audio_data:
                        st.subheader("Audio Response")
                        st.audio(audio_data, format="audio/wav")
                        
                        # Add download button for audio
                        st.download_button(
                            label="Download Audio",
                            data=audio_data,
                            file_name=f"response_{int(time.time())}.wav",
                            mime="audio/wav"
                        )
                    else:
                        st.warning("Audio was requested but could not be generated. See server logs for details.")
                
                # Display chat history
                st.subheader("Chat History")
                display_conversation()
        
        except Exception as e:
            error_msg = f"Unexpected error in frontend: {str(e)}"
            logger.error(error_msg, exc_info=True)
            st.error(error_msg)
            st.error("Please check the application logs for more information.")

# Add expandable debug section
with st.expander("Debug Information", expanded=False):
    if "request_history" in st.session_state and st.session_state.request_history:
        st.subheader("Recent Requests")
        for i, details in enumerate(reversed(st.session_state.request_history[-5:])):
            st.write(f"Request {i+1} - {time.strftime('%H:%M:%S', time.localtime(details.get('timestamp', 0)))}")
            # Filter out large data like traceback for display
            display_details = {k: v for k, v in details.items() if k != 'traceback' and not isinstance(v, bytes)}
            st.json(display_details)
    
    if st.button("Run Service Diagnostics"):
        with st.spinner("Running diagnostics..."):
            try:
                # Basic health check
                health_response = requests.get(f"{MEGASERVICE_URL}/health", timeout=5)
                st.write("Health Check:", "✅ OK" if health_response.status_code == 200 else "❌ Failed")
                
                # TTS info
                tts_info_response = requests.get(f"{MEGASERVICE_URL}/debug/tts-info", timeout=10)
                if tts_info_response.status_code == 200:
                    tts_info = tts_info_response.json()
                    st.write("TTS Service Info:")
                    st.json(tts_info)
                else:
                    st.write("TTS Service Info: ❌ Failed to retrieve")
            except Exception as e:
                st.error(f"Diagnostics failed: {str(e)}")

# Add to your app
if st.checkbox("Debug Mode"):
    st.write("Session State:", st.session_state)
    
    if st.button("Test Service Connection"):
        try:
            response = requests.get(f"{MEGASERVICE_URL}/health", timeout=5)
            st.json(response.json())
        except Exception as e:
            st.error(f"Connection error: {str(e)}")