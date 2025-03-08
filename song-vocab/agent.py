import os
import json
from typing import Dict, List, Optional, Any, Union
import ollama
from tools.search_web import search_web
from tools.get_page_content import get_page_content
from tools.extract_vocabulary import extract_vocabulary
from tools.generate_song_id import generate_song_id

class LyricsAgent:
    def __init__(self, model_name: str = "phi4-mini"):
        """Initialize the LyricsAgent with the specified model."""
        self.model_name = model_name
        self.prompt_file = os.path.join("prompts", "lyrics-agent.md")
        self.tools = {
            "search_web": search_web,
            "get_page_content": get_page_content,
            "extract_vocabulary": extract_vocabulary,
            "generate_song_id": generate_song_id
        }
        
    def _load_prompt(self) -> str:
        """Load the agent prompt from file."""
        try:
            with open(self.prompt_file, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # If the prompt file doesn't exist, return a default prompt
            return """
# Chinese Song Lyrics and Vocabulary Agent

You are an agent designed to find song lyrics in Putonghua (Mandarin Chinese) and extract vocabulary from them.

## Your Task
1. Search for the song lyrics based on the provided title and artist (if available)
2. Extract the correct lyrics from the search results
3. Format the lyrics cleanly
4. Extract vocabulary from the lyrics, including:
   - Chinese characters (simplified)
   - Pinyin
   - English translation

## Available Tools
- search_web: Search the web for song lyrics
- get_page_content: Get the content of a web page
- extract_vocabulary: Extract vocabulary from text
- generate_song_id: Generate a unique ID for a song

## Output Format
Return a JSON object with:
- lyrics: The full lyrics of the song
- vocabulary: A list of vocabulary items, each containing:
  - word: The Chinese word
  - jiantizi: The simplified form
  - pinyin: The pinyin representation
  - english: The English translation
"""

    def _parse_tool_calls(self, message: str) -> List[Dict[str, Any]]:
        """Parse tool calls from the agent's message."""
        tool_calls = []
        lines = message.split("\n")
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for tool call patterns like "I'll use the search_web tool to search for..."
            if any(tool in line.lower() for tool in self.tools.keys()):
                tool_name = None
                for t in self.tools.keys():
                    if t in line.lower():
                        tool_name = t
                        break
                
                # Try to find parameters in the following lines
                params = {}
                j = i + 1
                while j < len(lines) and not any(tool in lines[j].lower() for tool in self.tools.keys()):
                    param_line = lines[j].strip()
                    # Look for patterns like "query: ..." or "url: ..."
                    if ":" in param_line:
                        key, value = param_line.split(":", 1)
                        params[key.strip()] = value.strip()
                    j += 1
                
                if tool_name and params:
                    tool_calls.append({
                        "name": tool_name,
                        "parameters": params
                    })
                
                i = j - 1
            i += 1
        
        return tool_calls

    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tool calls and return the results."""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            parameters = tool_call["parameters"]
            
            if tool_name in self.tools:
                tool_func = self.tools[tool_name]
                try:
                    result = tool_func(**parameters)
                    results.append({
                        "tool": tool_name,
                        "parameters": parameters,
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "tool": tool_name,
                        "parameters": parameters,
                        "error": str(e)
                    })
        
        return results

    def run(self, message_request: str, artist_name: Optional[str] = None) -> Dict[str, Any]:
        """Run the agent to find lyrics and extract vocabulary."""
        system_prompt = self._load_prompt()
        
        # Create the initial message with the song request
        query = f"Find lyrics for the song: {message_request}"
        if artist_name:
            query += f" by {artist_name}"
        
        # Initial call to the LLM
        response = ollama.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        
        # Track conversation history
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
            {"role": "assistant", "content": response["message"]["content"]}
        ]
        
        # We'll use a React-like approach with multiple steps
        max_iterations = 10
        iterations = 0
        final_result = None
        
        while iterations < max_iterations and not final_result:
            # Parse tool calls from the agent's response
            tool_calls = self._parse_tool_calls(response["message"]["content"])
            
            if not tool_calls:
                # Check if we have a final result
                if "```json" in response["message"]["content"]:
                    # Extract the JSON output
                    json_start = response["message"]["content"].find("```json") + 7
                    json_end = response["message"]["content"].find("```", json_start)
                    json_str = response["message"]["content"][json_start:json_end].strip()
                    
                    try:
                        final_result = json.loads(json_str)
                        break
                    except json.JSONDecodeError:
                        # If JSON parsing fails, prompt the agent to format correctly
                        user_message = "Please provide the final result in valid JSON format with 'lyrics' and 'vocabulary' fields."
                else:
                    # Ask the agent to continue
                    user_message = "Please continue the process and use the tools to find the lyrics and extract vocabulary."
            else:
                # Execute the tools
                tool_results = self._execute_tools(tool_calls)
                
                # Create a message with the tool results
                tool_results_str = "Tool results:\n"
                for result in tool_results:
                    tool_results_str += f"\n## {result['tool']} ({result['parameters']})\n"
                    if "error" in result:
                        tool_results_str += f"Error: {result['error']}\n"
                    else:
                        if isinstance(result["result"], list):
                            tool_results_str += json.dumps(result["result"], ensure_ascii=False, indent=2)
                        else:
                            tool_results_str += str(result["result"])
                    tool_results_str += "\n"
                
                user_message = tool_results_str + "\nPlease continue with the next steps to find lyrics and extract vocabulary. When finished, return the result in JSON format."
            
            # Add the message to the conversation
            conversation.append({"role": "user", "content": user_message})
            
            # Get the next response
            response = ollama.chat(
                model=self.model_name,
                messages=conversation
            )
            
            # Add the response to the conversation
            conversation.append({"role": "assistant", "content": response["message"]["content"]})
            
            iterations += 1
        
        # If we didn't get a final result, try to extract it from the last response
        if not final_result:
            try:
                # Make a final attempt to parse JSON from the last response
                last_response = response["message"]["content"]
                
                # Try to find JSON blocks
                if "```json" in last_response:
                    json_start = last_response.find("```json") + 7
                    json_end = last_response.find("```", json_start)
                    json_str = last_response[json_start:json_end].strip()
                    
                    final_result = json.loads(json_str)
                else:
                    # If no JSON block, try to extract lyrics and vocabulary from the text
                    lyrics = "No lyrics found."
                    vocabulary = []
                    
                    # Make a direct call to extract_vocabulary with any text we have
                    conversation_text = " ".join([msg["content"] for msg in conversation if "content" in msg])
                    vocabulary = extract_vocabulary(conversation_text)
                    
                    final_result = {
                        "lyrics": lyrics,
                        "vocabulary": vocabulary
                    }
            except Exception as e:
                # Return an error result
                final_result = {
                    "lyrics": f"Error occurred: {str(e)}",
                    "vocabulary": []
                }
        
        return final_result

    def extract_vocabulary(self, text: str) -> List[Dict[str, Any]]:
        """Extract vocabulary from text."""
        return extract_vocabulary(text)