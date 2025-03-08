import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent import LyricsAgent

def test_agent():
    """Test the LyricsAgent with a sample song."""
    print("Testing LyricsAgent...")
    
    # Create agent
    agent = LyricsAgent()
    
    # Test with a well-known Chinese song
    song_request = "月亮代表我的心"
    artist_name = "邓丽君"  # Teresa Teng
    
    print(f"Searching for: {song_request} by {artist_name}")
    
    # Run the agent
    try:
        result = agent.run(song_request, artist_name)
        
        # Print the results
        print("\n=== LYRICS ===")
        print(result["lyrics"][:200] + "..." if len(result["lyrics"]) > 200 else result["lyrics"])
        
        print("\n=== VOCABULARY SAMPLE ===")
        for i, vocab in enumerate(result["vocabulary"][:5]):
            print(f"{i+1}. {vocab['word']} ({vocab['jiantizi']}) - {vocab['pinyin']} - {vocab['english']}")
        
        print(f"\nTotal vocabulary items: {len(result['vocabulary'])}")
        
        # Save results to a file
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"{song_request}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\nResults saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error testing agent: {str(e)}")
        return False

def test_vocabulary_extraction():
    """Test vocabulary extraction with a sample text."""
    print("\nTesting vocabulary extraction...")
    
    # Sample Chinese text
    sample_text = """
    月亮代表我的心
    你问我爱你有多深
    我爱你有几分
    你去想一想
    你去看一看
    月亮代表我的心
    """
    
    # Create agent
    agent = LyricsAgent()
    
    try:
        # Extract vocabulary
        vocabulary = agent.extract_vocabulary(sample_text)
        
        # Print results
        print("\n=== EXTRACTED VOCABULARY ===")
        for i, vocab in enumerate(vocabulary):
            print(f"{i+1}. {vocab['word']} ({vocab['jiantizi']}) - {vocab['pinyin']} - {vocab['english']}")
        
        print(f"\nTotal vocabulary items: {len(vocabulary)}")
        return True
    except Exception as e:
        print(f"Error testing vocabulary extraction: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_agent() and test_vocabulary_extraction()
    sys.exit(0 if success else 1)