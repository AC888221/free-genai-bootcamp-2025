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
import boto3
from botocore.config import Config

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

# Add Bedrock configuration after other configurations
BEDROCK_CONFIG = Config(
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    retries={
        'max_attempts': 3,
        'mode': 'standard'
    }
)

# Initialize Bedrock client
try:
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        config=BEDROCK_CONFIG
    )
    logger.info("Successfully initialized Bedrock client")
except Exception as e:
    logger.error(f"Failed to initialize Bedrock client: {str(e)}")
    bedrock_runtime = None

st.set_page_config(
    page_title="MegaTalk",
    page_icon="🤖",
    layout="wide",
)

# Title and description
st.title("MegaTalk")
st.markdown("### Your Language Buddy with Voice Response")

# Initialize session state for service status tracking
if "service_status" not in st.session_state:
    st.session_state.service_status = {
        "bedrock_service": {"status": "unknown", "last_check": None}
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

def call_bedrock_model(prompt: str, model_id: str = "anthropic.claude-v2") -> str:
    """Call AWS Bedrock model for text generation."""
    try:
        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
        })
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body.get('completion', '')
    except Exception as e:
        logger.error(f"Bedrock API error: {str(e)}")
        raise

def call_bedrock_tts(text: str, voice_id: str = "amazon.neural-text-to-speech") -> bytes:
    """Call AWS Bedrock for text-to-speech."""
    try:
        body = json.dumps({
            "text": text,
            "voice_id": voice_id,
            "engine": "neural"
        })
        
        response = bedrock_runtime.invoke_model(
            modelId=voice_id,
            body=body
        )
        
        return response.get('body').read()
    except Exception as e:
        logger.error(f"Bedrock TTS API error: {str(e)}")
        raise

def call_megaservice(text: str, params: Dict[str, Any]) -> Tuple[Optional[str], Optional[bytes], Optional[str], Dict[str, Any]]:
    """Modified to use Bedrock instead of custom service"""
    start_time = time.time()
    request_id = f"frontend_{int(start_time)}_{hash(text)}"
    details = {"request_id": request_id, "timestamp": start_time}
    
    try:
        # Prepare the prompt with HSK level
        system_prompt = """You are a friendly AI Putonghua buddy. Please answer all questions in Putonghua. Even if the user asks in English, please answer in Putonghua. Keep your answers friendly, and natural."""
        hsk_prompt = get_hsk_prompt(params.get("hsk_level", "HSK 1 (Beginner)"))
        full_prompt = f"{system_prompt}\n\n{hsk_prompt}\n\nUser: {text}\nAssistant:"
        
        # Get text response from Bedrock
        text_response = call_bedrock_model(full_prompt)
        details["response_time"] = time.time() - start_time
        
        # Generate audio if requested
        audio_data = None
        if params.get("generate_audio", True):
            try:
                audio_data = call_bedrock_tts(text_response)
                if audio_data:
                    audio_path = save_audio(audio_data, request_id)
                    details["audio_path"] = str(audio_path)
                    details["audio_size"] = len(audio_data)
            except Exception as e:
                logger.error(f"TTS generation failed: {str(e)}")
                details["tts_error"] = str(e)
        
        # Add to chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        chat_entry = {
            "timestamp": time.time(),
            "request_id": request_id,
            "user_input": text,
            "response": text_response,
            "audio_path": details.get("audio_path"),
            "details": details
        }
        st.session_state.chat_history.append(chat_entry)
        
        return text_response, audio_data, None, details
        
    except Exception as e:
        logger.exception(f"[{request_id}] Bedrock API error")
        details["error_type"] = "bedrock_api"
        details["error"] = str(e)
        return None, None, f"Bedrock API Error: {str(e)}", details

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
            display_details = {k: v for k, v in details.items() if k != 'traceback' and not isinstance(v, bytes)}
            st.json(display_details)
    
    if st.button("Run Service Diagnostics"):
        with st.spinner("Running diagnostics..."):
            try:
                # Test Bedrock connectivity
                test_response = call_bedrock_model("Test connection")
                st.write("Bedrock LLM Service:", "✅ OK")
                
                # Test TTS
                test_audio = call_bedrock_tts("Test audio")
                st.write("Bedrock TTS Service:", "✅ OK")
                
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