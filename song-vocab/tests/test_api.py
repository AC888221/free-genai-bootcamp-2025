import requests
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_endpoints():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"
    
    print("Testing API endpoints...")
    
    # Wait for the server to start
    server_ready = False
    max_retries = 5
    retries = 0
    
    while not server_ready and retries < max_retries:
        try:
            # Test the root endpoint
            response = requests.get(f"{base_url}/")
            if response.status_code == 200:
                server_ready = True
                print("Server is running")
            else:
                print(f"Server not ready yet (status code: {response.status_code}), retrying...")
                time.sleep(2)
                retries += 1
        except requests.exceptions.ConnectionError:
            print("Server not ready yet, retrying...")
            time.sleep(2)
            retries += 1
    
    if not server_ready:
        print("Server did not start in time, exiting")
        return False
    
    # Test the agent endpoint
    try:
        print("\nTesting /api/agent endpoint...")
        
        payload = {
            "message_request": "月亮代表我的心",
            "artist_name": "邓丽君"
        }
        
        response = requests.post(f"{base_url}/api/agent", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("Success! Sample of lyrics:")
            print(result["lyrics"][:200] + "..." if len(result["lyrics"]) > 200 else result["lyrics"])
            print(f"Number of vocabulary items: {len(result['vocabulary'])}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error testing agent endpoint: {str(e)}")
        return False
    
    # Test the vocabulary endpoint
    try:
        print("\nTesting /api/get_vocabulary endpoint...")
        
        payload = {
            "text": "月亮代表我的心\n你问我爱你有多深\n我爱你有几分"
        }
        
        response = requests.post(f"{base_url}/api/get_vocabulary", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("Success! Sample of vocabulary:")
            for i, vocab in enumerate(result["vocabulary"][:3]):
                print(f"{i+1}. {vocab['word']} - {vocab['pinyin']} - {vocab['english']}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error testing vocabulary endpoint: {str(e)}")
        return False
    
    print("\nAll API tests completed successfully")
    return True

if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)