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
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "90"))  # Longer timeout

st.set_page_config(
    page_title="OPEA MegaTalk",
    page_icon="🤖",
    layout="wide",
)

# Title and description
st.title("🤖 OPEA MegaTalk")
st.markdown("### Conversational AI with Voice Response")

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

def call_megaservice(text: str, params: Dict[str, Any]) -> Tuple[Optional[str], Optional[bytes], Optional[str], Dict[str, Any]]:
    """
    Call the megaservice with error handling and retries.
    Returns: (text_response, audio_data, error_message, details)
    """
    start_time = time.time()
    request_id = f"frontend_{int(start_time)}_{hash(text)}"
    details = {"request_id": request_id, "timestamp": start_time}
    
    try:
        logger.info(f"[{request_id}] Sending request to megaservice")
        
        with st.spinner("Processing request..."):
            response = requests.post(
                f"{MEGASERVICE_URL}/v1/megaservice",
                json={
                    "text": text,
                    "generate_audio": params.get("generate_audio", True),
                    "model": params.get("model", "Qwen/Qwen2.5-0.5B-Instruct"),
                    "temperature": params.get("temperature", 0.7),
                    "max_tokens": params.get("max_tokens", 1000),
                    "voice": params.get("voice", "default")
                },
                timeout=REQUEST_TIMEOUT
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
            
            # Handle audio data and potential errors
            audio_data = None
            if params.get("generate_audio", True):
                if data.get("audio_data"):
                    try:
                        audio_bytes = base64.b64decode(data["audio_data"])
                        audio_data = audio_bytes
                        details["audio_size"] = len(audio_bytes)
                        logger.info(f"[{request_id}] Successfully received audio response ({len(audio_bytes)} bytes)")
                    except Exception as e:
                        logger.error(f"[{request_id}] Audio decoding failed: {str(e)}")
                        details["audio_error"] = str(e)
                elif data.get("error_message"):
                    details["tts_error"] = data["error_message"]
                    logger.warning(f"[{request_id}] Audio generation issue: {data['error_message'][:200]}...")
            
            logger.info(f"[{request_id}] Request completed successfully in {details['response_time']:.2f}s")
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

if st.button("Submit"):
    if not user_input.strip():
        st.error("Please enter a message")
        logger.warning("Empty input submitted")
    else:
        try:
            request_params = {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "voice": voice,
                "generate_audio": generate_audio
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
                
                # Add to chat history
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []
                st.session_state.chat_history.append((user_input, text_response, audio_data))
        
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
            with st.expander(f"Request {i+1} - {time.strftime('%H:%M:%S', time.localtime(details.get('timestamp', 0)))}"):
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

# Display chat history if it exists
if "chat_history" in st.session_state and st.session_state.chat_history:
    st.subheader("Chat History")
    display_conversation()

def display_conversation():
    """Display the conversation history with audio playback"""
    for i, details in enumerate(reversed(st.session_state.conversation)):
        # Use columns instead of nested expanders
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"### Request {len(st.session_state.conversation) - i}")
            st.write(f"Time: {time.strftime('%H:%M:%S', time.localtime(details.get('timestamp', 0)))}")
            
            # Display the text response
            st.write("**Response:**")
            st.write(details.get("response", "No response available"))
            
            # Handle audio playback
            audio_path = details.get("audio_path")
            if audio_path:
                try:
                    # Construct the full path to the audio file
                    full_audio_path = Path("static") / audio_path
                    if full_audio_path.exists():
                        st.audio(str(full_audio_path), format="audio/mp3")
                    else:
                        st.warning("Audio file not found")
                except Exception as e:
                    st.error(f"Error playing audio: {str(e)}")
            else:
                st.info("No audio available for this response")
        
        # Add a divider between conversations
        st.divider()