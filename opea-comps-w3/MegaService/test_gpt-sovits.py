import pytest
import httpx
import logging
import os
import json
import time
from typing import Dict, Any, Optional, Union, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gptsovits_test.log")
    ]
)
logger = logging.getLogger(__name__)

# Test configuration
class TestConfig:
    # Base URLs
    GPT_SOVITS_URL = os.getenv("GPT_SOVITS_URL", "http://localhost:9880")
    
    # Test assets
    TEST_AUDIO_PATH = os.getenv("TEST_AUDIO_PATH", "test_assets/archive_jingyuan_1.wav")
    GPT_WEIGHTS_PATH = os.getenv("GPT_WEIGHTS_PATH", "GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt")
    SOVITS_WEIGHTS_PATH = os.getenv("SOVITS_WEIGHTS_PATH", "GPT_SoVITS/pretrained_models/s2G488k.pth")
    
    # Test parameters
    DEFAULT_LANGUAGE = "zh"
    DEFAULT_PROMPT = "测试语音合成"
    TIMEOUT = 30.0  # Longer timeout for TTS processing

class EndpointTest:
    """Base class for endpoint testing"""
    def __init__(self, base_url: str, timeout: float = TestConfig.TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        # Set larger limits for audio response handling
        self.client = httpx.Client(timeout=timeout, limits=httpx.Limits(max_connections=5))

    def test_endpoint(self, 
                     path: str, 
                     method: str = "GET", 
                     data: Optional[Dict[str, Any]] = None,
                     query_params: Optional[Dict[str, Any]] = None,
                     expect_binary: bool = False) -> Dict[str, Any]:
        """Test an endpoint and return results"""
        url = f"{self.base_url}{path}"
        
        # Include query parameters if provided
        if query_params:
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            url = f"{url}?{query_string}"
        
        result = {
            "endpoint": path,
            "method": method,
            "url": url,
            "status_code": None,
            "response": None,
            "error": None,
            "response_content_type": None,
            "response_size": None,
            "request_data": data,
            "request_params": query_params,
            "timestamp": time.time()
        }

        try:
            logger.info(f"Testing endpoint: {method} {url}")
            if data:
                logger.info(f"Request data: {json.dumps(data, ensure_ascii=False)}")
                
            if method == "GET":
                response = self.client.get(url)
            elif method == "POST":
                response = self.client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            result["status_code"] = response.status_code
            result["response_content_type"] = response.headers.get('content-type')
            result["response_size"] = len(response.content)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content type: {response.headers.get('content-type')}")
            
            # For binary responses (audio)
            if expect_binary or response.headers.get('content-type', '').startswith(('audio/', 'application/octet-stream')):
                if expect_binary and response.status_code == 200:
                    # Save the binary response to a file for inspection
                    output_dir = Path("test_results/audio")
                    output_dir.mkdir(exist_ok=True, parents=True)
                    timestamp = int(time.time())
                    file_ext = response.headers.get('content-type', '').split('/')[-1] or 'bin'
                    output_file = output_dir / f"response_{timestamp}.{file_ext}"
                    
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    
                    result["response"] = f"Binary data saved to {output_file} ({len(response.content)} bytes)"
                    logger.info(f"Binary response saved to {output_file}")
                else:
                    result["response"] = f"Binary data ({len(response.content)} bytes)"
            else:
                # Try to parse as JSON first
                try:
                    result["response"] = response.json()
                    logger.info(f"Response JSON: {json.dumps(result['response'], ensure_ascii=False)}")
                except:
                    # If not JSON, store as text
                    result["response"] = response.text
                    if len(response.text) > 1000:
                        logger.info(f"Response text: {response.text[:1000]}... (truncated)")
                    else:
                        logger.info(f"Response text: {response.text}")

            # Check for error status codes
            if response.status_code >= 400:
                result["error"] = f"HTTP error {response.status_code}"
                logger.error(f"Error response {response.status_code}: {result['response']}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing {url}: {str(e)}")

        return result

    def close(self):
        """Close the HTTP client"""
        self.client.close()

def test_gpt_sovits_tts_get(tester: EndpointTest) -> Dict[str, Any]:
    """Test the TTS GET endpoint"""
    logger.info("Testing TTS GET endpoint...")
    
    # Required parameters
    params = {
        "text": "这是一个测试语音合成的例子",
        "text_lang": TestConfig.DEFAULT_LANGUAGE,
        "ref_audio_path": TestConfig.TEST_AUDIO_PATH,
        "prompt_lang": TestConfig.DEFAULT_LANGUAGE,
        "prompt_text": TestConfig.DEFAULT_PROMPT,
        "text_split_method": "cut5",
        "batch_size": "1",
        "media_type": "wav",
        "streaming_mode": "false"
    }
    
    # Test with minimal required parameters
    result = tester.test_endpoint(
        path="/tts",
        method="GET",
        query_params=params,
        expect_binary=True
    )
    
    return result

def test_gpt_sovits_tts_post(tester: EndpointTest) -> Dict[str, Any]:
    """Test the TTS POST endpoint"""
    logger.info("Testing TTS POST endpoint...")
    
    # Test data with all parameters
    data = {
        "text": "这是一个通过POST请求测试语音合成的例子",
        "text_lang": TestConfig.DEFAULT_LANGUAGE,
        "ref_audio_path": TestConfig.TEST_AUDIO_PATH,
        "prompt_text": TestConfig.DEFAULT_PROMPT,
        "prompt_lang": TestConfig.DEFAULT_LANGUAGE,
        "top_k": 5,
        "top_p": 1.0,
        "temperature": 1.0,
        "text_split_method": "cut5",
        "batch_size": 1,
        "batch_threshold": 0.75,
        "split_bucket": True,
        "speed_factor": 1.0,
        "media_type": "wav",
        "streaming_mode": False,
        "parallel_infer": True,
        "repetition_penalty": 1.35
    }
    
    result = tester.test_endpoint(
        path="/tts",
        method="POST",
        data=data,
        expect_binary=True
    )
    
    return result

def test_gpt_sovits_model_weights(tester: EndpointTest) -> List[Dict[str, Any]]:
    """Test the model weights endpoints"""
    logger.info("Testing model weights endpoints...")
    
    results = []
    
    # Test GPT weights endpoint
    gpt_params = {
        "weights_path": TestConfig.GPT_WEIGHTS_PATH
    }
    
    gpt_result = tester.test_endpoint(
        path="/set_gpt_weights",
        method="GET",
        query_params=gpt_params
    )
    results.append(gpt_result)
    
    # Test SoVITS weights endpoint
    sovits_params = {
        "weights_path": TestConfig.SOVITS_WEIGHTS_PATH
    }
    
    sovits_result = tester.test_endpoint(
        path="/set_sovits_weights",
        method="GET",
        query_params=sovits_params
    )
    results.append(sovits_result)
    
    return results

def test_gpt_sovits_control(tester: EndpointTest) -> Dict[str, Any]:
    """Test the control endpoint (careful: this will restart the service)"""
    logger.info("Testing control endpoint...")
    
    # Only use this for testing - will restart the service
    # For safety, we're using a mock value that won't actually trigger restart
    # Change 'mock_restart' to 'restart' to actually test restart functionality
    params = {
        "command": "mock_restart"  # Use "restart" to actually restart the service
    }
    
    result = tester.test_endpoint(
        path="/control",
        method="GET",
        query_params=params
    )
    
    return result

def file_exists(file_path: str) -> bool:
    """Check if a file exists and log the result"""
    exists = os.path.isfile(file_path)
    logger.info(f"Checking file: {file_path} - {'Exists' if exists else 'Not found'}")
    return exists

def check_prerequisites():
    """Check if all required files exist"""
    logger.info("Checking prerequisites...")
    
    missing_files = []
    
    # Check test audio file
    if not file_exists(TestConfig.TEST_AUDIO_PATH):
        missing_files.append(TestConfig.TEST_AUDIO_PATH)
    
    # Check model weight files
    if not file_exists(TestConfig.GPT_WEIGHTS_PATH):
        missing_files.append(TestConfig.GPT_WEIGHTS_PATH)
    
    if not file_exists(TestConfig.SOVITS_WEIGHTS_PATH):
        missing_files.append(TestConfig.SOVITS_WEIGHTS_PATH)
    
    if missing_files:
        logger.warning(f"Missing required files: {missing_files}")
        return False
    
    return True

def check_service_availability(tester: EndpointTest) -> bool:
    """Check if the GPT-SoVITS service is available"""
    logger.info(f"Checking if service is available at {tester.base_url}...")
    
    try:
        # Simple health check - try to connect to the service
        response = tester.client.get(tester.base_url)
        logger.info(f"Service responded with status code: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Service unavailable: {str(e)}")
        return False

def save_test_results(results: Dict[str, Any], filename: str = "gptsovits_test_results.json"):
    """Save test results to a file"""
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / filename
    
    # Convert any non-serializable values to strings
    def sanitize_for_json(obj):
        if isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_for_json(i) for i in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    sanitized_results = sanitize_for_json(results)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sanitized_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Test results saved to {output_path}")

def main():
    """Run all GPT-SoVITS tests"""
    logger.info("Starting GPT-SoVITS endpoint tests")
    
    # Initialize the tester
    tester = EndpointTest(TestConfig.GPT_SOVITS_URL)
    
    try:
        # Check prerequisites
        prereqs_ok = check_prerequisites()
        if not prereqs_ok:
            logger.warning("Some prerequisites are missing but continuing anyway")
        
        # Check service availability
        service_available = check_service_availability(tester)
        if not service_available:
            logger.error("GPT-SoVITS service is not available. Aborting tests.")
            return
        
        # Run the tests
        results = {
            "timestamp": time.time(),
            "config": {
                "service_url": TestConfig.GPT_SOVITS_URL,
                "test_audio_path": TestConfig.TEST_AUDIO_PATH,
                "gpt_weights_path": TestConfig.GPT_WEIGHTS_PATH,
                "sovits_weights_path": TestConfig.SOVITS_WEIGHTS_PATH
            },
            "prerequisites_check": prereqs_ok,
            "service_available": service_available,
            "tests": {}
        }
        
        # Test TTS GET endpoint
        results["tests"]["tts_get"] = test_gpt_sovits_tts_get(tester)
        
        # Test TTS POST endpoint
        results["tests"]["tts_post"] = test_gpt_sovits_tts_post(tester)
        
        # Test model weights endpoints
        model_results = test_gpt_sovits_model_weights(tester)
        results["tests"]["set_gpt_weights"] = model_results[0]
        results["tests"]["set_sovits_weights"] = model_results[1]
        
        # Test control endpoint (commented out to avoid restart)
        # results["tests"]["control"] = test_gpt_sovits_control(tester)
        
        # Save results
        save_test_results(results)
        
        # Print summary
        print("\nTest Summary:")
        print("=" * 50)
        for test_name, test_result in results["tests"].items():
            status = test_result.get("status_code", "N/A")
            if test_result.get("error"):
                print(f"{test_name}: ❌ Error - {test_result['error']}")
            elif status == 200:
                print(f"{test_name}: ✅ Success")
            else:
                print(f"{test_name}: ⚠️ Status {status}")
        
        logger.info("All tests completed")
    
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}", exc_info=True)
    
    finally:
        # Clean up resources
        tester.close()

if __name__ == "__main__":
    main()