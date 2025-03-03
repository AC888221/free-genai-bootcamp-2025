# Putonghua Language Learning App

## Key Features

- **Three-state workflow**: Setup → Practice → Review
- **Chinese language support**: Characters and Pinyin representation
- **Audio playback**: Text-to-speech for pronunciation practice
- **Image upload**: For submitting handwritten Chinese characters
- **OCR integration**: Using EasyOCR for character recognition
- **Detailed feedback**: Character-by-character comparison
- **Grading system**: A-B-C-D ranking with color coding

Grading Criteria
Stroke Order: Correct sequence of strokes.
Accuracy: Precision in forming each character.
Completeness: All parts of the character are present and correctly formed.
Neatness: Overall tidiness and readability of the handwriting.
Grading Scale
A (Excellent):

Stroke order is perfect.
Characters are accurately formed with no mistakes.
All parts of the characters are present and correctly formed.
Handwriting is neat and easy to read.
B (Good):

Minor mistakes in stroke order.
Characters are mostly accurate with few minor errors.
Most parts of the characters are present and correctly formed.
Handwriting is generally neat but may have slight inconsistencies.
C (Average):

Several mistakes in stroke order.
Characters have noticeable errors but are still recognizable.
Some parts of the characters are missing or incorrectly formed.
Handwriting is legible but not very neat.
D (Needs Improvement):

Many mistakes in stroke order.
Characters are poorly formed and difficult to recognize.
Many parts of the characters are missing or incorrectly formed.
Handwriting is messy and hard to read.
F (Fail):

Stroke order is incorrect.
Characters are unrecognizable.
Most parts of the characters are missing or incorrectly formed.
Handwriting is very messy and illegible.

## How to Run the App

1. Save the code to a file named `app.py`.
2. Install the required dependencies:
   ```bash
   pip install streamlit pillow gtts easyocr numpy pandas boto3
   ```
3. Set up your AWS credentials:
   - You can enter them directly in the app's sidebar.
   - Or set them as environment variables before running.
4. Run the app with:
   ```bash
   streamlit run app.py
   ```

## Implementation Notes

- The app includes mock data and functions since we don't have access to actual APIs.
- For a production version, you would replace:
  - The mock word collection with actual API calls.
  - The hardcoded sentences with LLM-generated content.
  - The simplified grading with more advanced OCR and LLM assessment.

## Claude 3 Haiku Integration

### AWS Configuration

- **AWS credentials input**: In the sidebar (hidden by default).
- **Region selection dropdown**.
- **Secure password input** for credentials.

### Bedrock Client Setup

- Added `boto3` integration for Amazon Bedrock.
- Created a function to call Claude 3 Haiku specifically.
- Set up appropriate error handling for API calls.

### LLM-powered Functions

- **Sentence generation**: Uses Claude 3 Haiku to create Chinese sentences based on vocabulary words.
- **Grading and feedback**: Uses Claude to analyze handwritten submissions and provide educational feedback.

## Cost-Saving Measures

- **Cached results**: Used Streamlit's caching to prevent redundant API calls. Implemented fallback mechanisms if API calls fail.
- **Optimized prompts**: Short, focused prompts to minimize token usage. Low temperature settings (0.1-0.3) for more deterministic responses. Structured JSON outputs to reduce parsing complexity.
- **Efficient Claude usage**: Only using Claude for high-value tasks (sentence generation and grading). Keeping local processing for simpler tasks.

### Technical Requirements

- **Streamlit**
- **MangaOCR** (Japanese) or another language using Managed LLM with Vision (e.g., GPT-4)
- Be able to upload an image

### Kana Practice Apps (Hard Requirement)

- Use a Vision Encoder Decoder for your target language (e.g., Toki Pona, Japanese, Chinese).
- Be able to input your image via webcam, upload, or draw.
- Decide on what you want to evaluate: Sentence, Word, Character.

### Technical Uncertainties and Suggestions

- **Vision Encoder Decoder Integration**:
  - **Uncertainty**: Integrating a Vision Encoder Decoder model for recognizing characters in various languages.
  - **Suggestion**: Use pre-trained models like Tesseract OCR for initial testing and then fine-tune a Vision Transformer (ViT) model for better accuracy.
- **Image Input Handling**:
  - **Uncertainty**: Allowing users to input images via webcam, upload, or drawing.
  - **Suggestion**: Implement a multi-input system using libraries like OpenCV for webcam capture, Streamlit for file uploads, and a drawing canvas using HTML5 Canvas or a library like Fabric.js.
- **Evaluation Criteria**:
  - **Uncertainty**: Deciding what to evaluate (sentence, word, character).
  - **Suggestion**: Start with character recognition to build a robust foundation, then expand to word and sentence evaluation. Use a modular approach to easily add new evaluation criteria.
- **Language-Specific Challenges**:
  - **Uncertainty**: Handling the nuances of different languages (e.g., stroke order in Japanese, tonal differences in Chinese).
  - **Suggestion**: Incorporate language-specific preprocessing steps, such as stroke order verification for Japanese or tone detection for Chinese, using specialized libraries or custom algorithms.
- **User Interface and Experience**:
  - **Uncertainty**: Designing an intuitive and user-friendly interface.
  - **Suggestion**: Use a framework like Streamlit for rapid prototyping and gather user feedback to iteratively improve the UI. Ensure the interface supports all input methods seamlessly.
- **Performance and Scalability**:
  - **Uncertainty**: Ensuring the app performs well with various input types and scales efficiently.
  - **Suggestion**: Optimize the Vision Encoder Decoder model for speed and accuracy, and use cloud services like AWS or Google Cloud for scalable backend processing.

## Project Structure

- `app.py`: The main entry point for your Streamlit app, integrating all the modules.
- `config.py`: Configuration settings.
- `frontend/`: Contains files related to the frontend logic and styling.
  - `styling.py`: Contains the CSS styling for the app.
  - `state_management.py`: Manages the state transitions and session state.
- `backend/`: Contains files related to the backend logic and data processing.
  - `ocr_reader.py`: Initializes the OCR reader.
  - `bedrock_client.py`: Initializes the Bedrock client.
  - `claude_haiku.py`: Handles API calls to Claude Haiku.
  - `word_collection.py`: Fetches the word collection.
  - `sentence_generation.py`: Generates sentences.
  - `audio_generation.py`: Generates audio files.
  - `image_processing.py`: Processes and grades images.