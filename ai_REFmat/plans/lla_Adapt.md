# Plan to Convert Japanese Language Learning Application to Putonghua Learning Application

## Steps to Follow

### 1. Content Adaptation
- [ ] **Update Language Resources**
  - Replace all Japanese language resources with equivalent Putonghua resources.
  
- [ ] **Modify YouTube Transcript Downloader**
  - Update the `YouTubeTranscriptDownloader` class to support Putonghua transcripts.
  - Change the default languages to include Mandarin:
    ```python
    class YouTubeTranscriptDownloader:
        def __init__(self, languages: List[str] = ["zh-Hans", "en"]):
            self.languages = languages
    ```

- [ ] **Update Example Questions**
  - Change example questions in the chat interface to reflect Putonghua queries.

### 2. User Interface Changes
- [ ] **Change UI Text and Labels**
  - Update all UI text, labels, and instructions from Japanese to Putonghua.

- [ ] **Update Character Count Functionality**
  - Modify the `count_characters` function to count Mandarin characters:
    ```python
    def is_chinese(char):
        return '\u4e00' <= char <= '\u9fff'  # Check for Chinese characters
    ```

- [ ] **Revise Stage Descriptions**
  - Modify sidebar descriptions to focus on Putonghua learning.

### 3. Backend Adjustments
- [ ] **Ensure Chat Functionality Supports Putonghua**
  - Test the `BedrockChat` class with Putonghua queries and responses.

- [ ] **Review Data Storage**
  - Check the SQLite database schema for compatibility with Putonghua content.

### 4. Error Handling and Debugging
- [ ] **Update Error Messages**
  - Change error messages to be relevant to Putonghua.

- [ ] **Implement Testing**
  - Write tests to ensure all functionalities work with Putonghua content:
    ```python
    def test_transcript_download():
        downloader = YouTubeTranscriptDownloader()
        transcript = downloader.get_transcript("https://www.youtube.com/watch?v=example")
        assert transcript is not None, "Transcript should not be None"
    ```

### 5. Interactive Features
- [ ] **Create New Practice Scenarios**
  - Develop interactive scenarios focusing on Putonghua.

- [ ] **Ensure Audio Synthesis Supports Putonghua**
  - Test text-to-speech functionality for Mandarin.

### 6. Documentation and User Guidance
- [ ] **Update README.md**
  - Revise the README file to reflect the new focus on Putonghua.

- [ ] **Provide User Guidance**
  - Create clear instructions for using the application for Putonghua learning.

### 7. Deployment and Feedback
- [ ] **Deploy Updated Application**
  - Deploy the application and monitor for issues.

- [ ] **Gather User Feedback**
  - Collect feedback to identify areas for improvement.

### 8. Future Enhancements
- [ ] **Consider Additional Language Support**
  - Plan for future support of other dialects or languages.

- [ ] **Encourage Community Contributions**
  - Create a section for user contributions to enhance content quality.

## Testing Code Example
Here’s a simple test case to ensure the transcript downloader works correctly:
```python
def test_transcript_download():
    downloader = YouTubeTranscriptDownloader()
    transcript = downloader.get_transcript("https://www.youtube.com/watch?v=example")
    assert transcript is not None, "Transcript should not be None"
```