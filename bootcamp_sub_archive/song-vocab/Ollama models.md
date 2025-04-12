Model Recommendation for Ollama on Your System
Based on your hardware specifications (Intel i7-8650U CPU with 32GB RAM and no GPU), you'll want a smaller, efficient model that can run well on CPU while still providing good performance.
Best Options for Your System
Phi4-mini (3.8B) - Excellent choice
Very recent (updated 7 days ago)
Small size (3.8B parameters)
Includes function calling capability
Good balance of performance and resource requirements
Phi3-mini (3.8B)
https://ollama.com/library/phi3
Small, efficient model
Good performance for its size
Updated 10 months ago
Gemma2 (2B)
Very compact model from Google
Good performance for general tasks
Updated 7 months ago
4. SmolLM2 (1.7B)
Ultra-lightweight option
Has tools capability
Updated 4 months ago
Llama3.2 (1B or 3B)
Meta's smaller models
Good general performance
Updated 5 months ago
Top Recommendation
Phi4-mini (3.8B) would be my top recommendation because:
It's the most recently updated (7 days ago)
It specifically supports function calling (important for agent development)
The 3.8B parameter size should run reasonably well on your CPU
Microsoft's Phi models are known for excellent performance despite their small size
Your 32GB RAM should be sufficient to run this model, though you may need to adjust context length settings if you encounter memory issues.


Requirements for Phi4-mini (3.8B)
Based on the information available, here are the general requirements for running Phi4-mini (3.8B) on Ollama:
Hardware Requirements
CPU: Your Intel i7-8650U CPU should be sufficient
RAM: Minimum 8GB, but your 32GB is more than adequate
Storage: At least 5-10GB free space for the model files
GPU: Not required (can run on CPU only, which matches your setup)
Software Requirements
Operating System: Windows, macOS, or Linux with Ollama installed
Ollama: Latest version recommended for best compatibility
Performance Expectations
Inference Speed: Expect 1-3 tokens per second on CPU (varies based on prompt length and settings)
Context Length: Supports standard context window (likely 4K-8K tokens)
Memory Usage: Typically 6-8GB RAM during operation
Disk Space: The model will require approximately 2-4GB of storage
Recommended Settings
When running on CPU only, you might want to:
Use a smaller context length setting if you experience memory issues
Consider running with reduced precision (like int8 quantization) for better performance
Adjust temperature and other generation parameters to balance quality and speed
The Phi4-mini model should run reasonably well on your system, especially with your generous 32GB RAM allocation. The model is designed to be efficient while still providing good capabilities, including the function calling feature that will be useful for your agent development.