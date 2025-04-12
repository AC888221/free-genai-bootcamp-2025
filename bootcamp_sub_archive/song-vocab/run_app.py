import subprocess
import sys
import time
import os

def run_backend():
    print("Starting FastAPI backend...")
    backend_process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Give the backend time to start
    time.sleep(3)
    return backend_process

def run_frontend():
    print("Starting Streamlit frontend...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return frontend_process

def main():
    try:
        # Start the backend
        backend_process = run_backend()
        
        # Start the frontend
        frontend_process = run_frontend()
        
        print("Both applications are running!")
        print("Access the Streamlit frontend at http://localhost:8501")
        print("Press Ctrl+C to stop both applications")
        
        # Keep the script running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down applications...")
        
    finally:
        # Clean up processes
        if 'backend_process' in locals():
            backend_process.terminate()
        if 'frontend_process' in locals():
            frontend_process.terminate()
        
        print("Applications stopped.")

if __name__ == "__main__":
    main() 