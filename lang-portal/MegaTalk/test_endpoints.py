import pytest
import httpx
import logging
import os
import json
from typing import Dict, Any
from pathlib import Path
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
class TestConfig:
    # Using environment variables for configuration
    MEGASERVICE_URL = os.getenv("MEGASERVICE_URL", "http://localhost:9500")
    VLLM_URL = os.getenv("LLM_ENDPOINT", "http://localhost:8008")
    TTS_URL = os.getenv("TTS_ENDPOINT", "http://localhost:9088")
    GPT_SOVITS_URL = f"http://localhost:{os.getenv('GPT_SOVITS_PORT', '9880')}"
    
    # Container information for reference
    CONTAINERS = {
        "megaservice": {"name": "opea-megaservice", "port": int(os.getenv("MEGASERVICE_PORT", 9500))},
        "vllm": {"name": "vllm-openvino-arc", "port": int(os.getenv("LLM_ENDPOINT_PORT", 8008))},
        "tts": {"name": "tts-gptsovits-service", "port": int(os.getenv("TTS_PORT", 9088))},
        "gpt_sovits": {"name": "gpt-sovits-service", "port": int(os.getenv("GPT_SOVITS_PORT", 9880))}
    }

    # TTS default configuration from environment
    TTS_DEFAULT_CONFIG = {
        "ref_wav": os.getenv("TTS_DEFAULT_REF_WAV", "welcome_cn.wav"),
        "prompt": os.getenv("TTS_DEFAULT_PROMPT", "欢迎使用"),
        "language": os.getenv("TTS_DEFAULT_LANGUAGE", "zh")
    }
    
    TIMEOUT = 10.0

    # GPT-SoVITS specific configuration
    GPT_SOVITS_CONFIG = {
        "ref_audio_path": "archive_jingyuan_1.wav",
        "prompt_text": "我是「罗浮」云骑将军景元",
        "text_split_method": "cut5",
        "batch_size": 1,
        "media_type": "wav",
        "streaming_mode": False,
        "gpt_weights": "GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt",
        "sovits_weights": "GPT_SoVITS/pretrained_models/s2G488k.pth"
    }

class EndpointTest:
    """Base class for endpoint testing"""
    def __init__(self, base_url: str, timeout: float = TestConfig.TIMEOUT, max_retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=timeout)

    def test_endpoint(self, path: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test an endpoint and return results with retry logic"""
        url = f"{self.base_url}{path}"
        result = {
            "endpoint": path,
            "method": method,
            "url": url,
            "status_code": None,
            "response": None,
            "error": None,
            "response_content": None
        }

        for attempt in range(self.max_retries):
            try:
                if method == "GET":
                    response = self.client.get(url)
                elif method == "POST":
                    response = self.client.post(url, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                result["status_code"] = response.status_code
                result["response_content"] = response.text
                try:
                    result["response"] = response.json()
                except:
                    # For binary responses like audio
                    if response.headers.get('content-type', '').startswith('audio/'):
                        result["response"] = f"Audio data ({len(response.content)} bytes)"
                    else:
                        result["response"] = response.text if response.text else None
                
                # If we get here, the request was successful
                break

            except httpx.TimeoutException as e:
                error_msg = f"Timeout on attempt {attempt + 1}/{self.max_retries}"
                logger.warning(f"{error_msg} for {url}")
                if attempt == self.max_retries - 1:  # Last attempt
                    result["error"] = error_msg
                    logger.error(f"Final timeout error for {url}: {str(e)}")
                else:
                    time.sleep(1)  # Wait before retry
                continue
                
            except Exception as e:
                result["error"] = str(e)
                logger.error(f"Error testing {url}: {str(e)}")
                break

        return result

@pytest.fixture
def megaservice_test():
    return EndpointTest(TestConfig.MEGASERVICE_URL)

@pytest.fixture
def vllm_test():
    return EndpointTest(TestConfig.VLLM_URL)

@pytest.fixture
def tts_test():
    return EndpointTest(TestConfig.TTS_URL)

@pytest.fixture
def gpt_sovits_test():
    return EndpointTest(TestConfig.GPT_SOVITS_URL)

def test_megaservice_endpoints(megaservice_test):
    """Test MegaService endpoints"""
    endpoints = [
        {"path": "/", "method": "GET"},
        {"path": "/health", "method": "GET"},
        {"path": "/v1/megaservice", "method": "POST", "data": {
            "text": "Hello, world!",
            "model": "Qwen/Qwen2.5-0.5B-Instruct",
            "generate_audio": True
        }},
        {"path": "/v1/audio/files", "method": "GET"},
        {"path": "/debug/tts-info", "method": "GET"}
    ]

    results = []
    for endpoint in endpoints:
        result = megaservice_test.test_endpoint(
            endpoint["path"], 
            endpoint["method"],
            endpoint.get("data")
        )
        results.append(result)
        logger.info(f"MegaService {endpoint['path']}: {result['status_code']}")
    
    return results

def test_vllm_endpoints(vllm_test):
    """Test VLLM endpoints"""
    endpoints = [
        {"path": "/health", "method": "GET"},
        {"path": "/v1/chat/completions", "method": "POST", "data": {
            "model": "Qwen/Qwen2.5-0.5B-Instruct",
            "messages": [{"role": "user", "content": "Hello"}]
        }},
        {"path": "/v1/completions", "method": "POST", "data": {
            "model": "Qwen/Qwen2.5-0.5B-Instruct",
            "prompt": "Hello, world!"
        }},
        {"path": "/v1/embeddings", "method": "POST", "data": {
            "model": "Qwen/Qwen2.5-0.5B-Instruct",
            "input": "Hello, world!"
        }}
    ]

    results = []
    for endpoint in endpoints:
        result = vllm_test.test_endpoint(
            endpoint["path"], 
            endpoint["method"],
            endpoint.get("data")
        )
        results.append(result)
        logger.info(f"VLLM {endpoint['path']}: {result['status_code']}")
    
    return results

def test_tts_endpoints(tts_test):
    """Test TTS endpoints with environment configuration"""
    # Use GPT_SOVITS_URL directly in tests
    endpoints = [
        {"path": "/health", "method": "GET"},
        
        # Test with simple English text
        {"path": "/v1/audio/speech", "method": "POST", "data": {
            "input": "Who are you?"
        }},
        
        # Test with Chinese text
        {"path": "/v1/audio/speech", "method": "POST", "data": {
            "input": "你好世界"
        }}
    ]
    
    results = []
    for endpoint in endpoints:
        result = tts_test.test_endpoint(
            f"{TestConfig.GPT_SOVITS_URL}{endpoint['path']}",  # Directly using GPT_SOVITS_URL
            endpoint["method"],
            endpoint.get("data")
        )
        
        logger.info(f"\nTesting TTS endpoint: {endpoint['method']} {endpoint['path']}")
        logger.info(f"Request data: {endpoint.get('data')}")
        logger.info(f"Status: {result['status_code']}")
        
        if result['status_code'] == 200:
            if isinstance(result['response'], str) and 'Audio data' in result['response']:
                logger.info(result['response'])
            else:
                logger.info(f"Response: {result.get('response', 'No response content')}")
        else:
            logger.info(f"Response content: {result.get('response_content', 'None')}")
        
        if result.get('error'):
            logger.error(f"Error: {result['error']}")
        
        results.append(result)
    
    return results

def get_tts_logs():
    """Fetch recent logs from TTS container"""
    try:
        import subprocess
        cmd = "docker logs tts-gptsovits-service --tail 50"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        if process.returncode == 0:
            return output.decode('utf-8')
        else:
            return f"Error fetching logs: {error.decode('utf-8')}"
    except Exception as e:
        return f"Failed to get logs: {str(e)}"

def save_test_results(results: Dict[str, Any], filename: str = "endpoint_test_results.json"):
    """Save test results to a file"""
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / filename
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to {output_path}")

def check_network_connectivity():
    """Check network connectivity to services"""
    import socket
    
    services = {
        "megaservice": TestConfig.MEGASERVICE_URL,
        "vllm": TestConfig.VLLM_URL,
        "tts": TestConfig.TTS_URL
    }
    
    results = {}
    for name, url in services.items():
        try:
            # Extract hostname from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            
            # Try to connect
            sock = socket.create_connection((hostname, port), timeout=5)
            sock.close()
            results[name] = {"status": "success", "url": url}
        except Exception as e:
            results[name] = {"status": "error", "url": url, "error": str(e)}
    
    return results

def check_container_health():
    """Check Docker container health status"""
    import subprocess
    import json
    
    results = {}
    for service, info in TestConfig.CONTAINERS.items():
        try:
            # Get container health status
            cmd = f"docker inspect --format='{{{{json .State.Health}}}}' {info['name']}"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            
            if process.returncode == 0 and output:
                health_info = json.loads(output.decode('utf-8'))
                results[service] = {
                    "container": info['name'],
                    "port": info['port'],
                    "status": health_info.get('Status', 'unknown'),
                    "last_check": health_info.get('Log', [{}])[-1].get('End', ''),
                    "failure_count": len([log for log in health_info.get('Log', []) 
                                       if log.get('ExitCode', 0) != 0])
                }
            else:
                results[service] = {
                    "container": info['name'],
                    "port": info['port'],
                    "status": "error",
                    "error": error.decode('utf-8') if error else "No health check configured"
                }
        except Exception as e:
            results[service] = {
                "container": info['name'],
                "port": info['port'],
                "status": "error",
                "error": str(e)
            }
    
    return results

def test_gpt_sovits_endpoints(gpt_sovits_test):
    """Test GPT-SoVITS endpoints"""
    
    # Test endpoints
    endpoints = [
        # 1. Health check
        {"path": "/health", "method": "GET"},
        
        # 2. TTS endpoint with simple text input
        {"path": "/v1/audio/speech", "method": "POST", "data": {
            "input": "Who are you?"
        }},
        
        # 3. TTS endpoint with Chinese text
        {"path": "/v1/audio/speech", "method": "POST", "data": {
            "input": "你好世界"
        }},
        
        # 4. Model info endpoint
        {"path": "/v1/info", "method": "GET"}
    ]
    
    results = []
    logger.info("\nTesting GPT-SoVITS endpoints:")
    logger.info("=" * 50)
    
    for endpoint in endpoints:
        try:
            result = gpt_sovits_test.test_endpoint(
                endpoint["path"], 
                endpoint["method"],
                endpoint.get("data")
            )
            
            results.append(result)
            logger.info(f"\nTesting GPT-SoVITS endpoint: {endpoint['method']} {endpoint['path']}")
            logger.info(f"Request data: {endpoint.get('data')}")
            logger.info(f"Status: {result['status_code']}")
            
            if result['status_code'] == 200:
                if isinstance(result['response'], str) and 'Audio data' in result['response']:
                    logger.info(result['response'])
                else:
                    logger.info(f"Response: {result.get('response', 'No response content')}")
            else:
                logger.error(f"Error details: {result.get('response_content', '')}")
        
        except Exception as e:
            logger.error(f"Error testing endpoint {endpoint['path']}: {str(e)}")
            results.append({
                "endpoint": endpoint["path"],
                "method": endpoint["method"],
                "status_code": None,
                "error": str(e)
            })
    
    return results
    
def main():
    """Run all tests and save results"""
    try:
        # Check container health first
        print("\nChecking Container Health:")
        print("=" * 50)
        health_status = check_container_health()
        for service, info in health_status.items():
            status = f"✅ {info['status']}" if info['status'] == 'healthy' else f"❌ {info['status']}"
            print(f"{service} ({info['container']}):")
            print(f"  Status: {status}")
            print(f"  Port: {info['port']}")
            if 'error' in info:
                print(f"  Error: {info['error']}")
            print()
        
        # Continue with network connectivity check
        print("\nChecking Network Connectivity:")
        print("=" * 50)
        connectivity = check_network_connectivity()
        for service, info in connectivity.items():
            status = "✅ Connected" if info["status"] == "success" else f"❌ Failed: {info.get('error')}"
            print(f"{service}: {status}")
            print(f"URL: {info['url']}\n")
        
        # Get TTS logs before testing
        print("\nFetching TTS Service Logs:")
        print("=" * 50)
        tts_logs = get_tts_logs()
        print(tts_logs)
        
        # Run endpoint tests
        print("\nRunning Endpoint Tests:")
        print("=" * 50)
        
        results = {
            "container_health": health_status,
            "network_check": connectivity,
            "tts_logs": tts_logs,
            "megaservice": test_megaservice_endpoints(EndpointTest(TestConfig.MEGASERVICE_URL)),
            "vllm": test_vllm_endpoints(EndpointTest(TestConfig.VLLM_URL)),
            "tts": test_tts_endpoints(EndpointTest(TestConfig.TTS_URL)),
            "gpt_sovits": test_gpt_sovits_endpoints(EndpointTest(TestConfig.GPT_SOVITS_URL))
        }
        
        save_test_results(results)
        
        # Print endpoint test summary
        print("\nEndpoint Test Summary:")
        print("=" * 50)
        for service, service_results in results.items():
            if service not in ["container_health", "network_check", "tts_logs"]:
                print(f"\n{service.upper()}:")
                for result in service_results:
                    status = result['status_code'] if result['status_code'] else 'ERROR'
                    print(f"{result['method']} {result['endpoint']}: {status}")
                    if result['error']:
                        print(f"  Error: {result['error']}")
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()