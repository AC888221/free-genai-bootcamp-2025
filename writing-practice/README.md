I've created a complete Streamlit application for Putonghua language learning based on the technical specification. This app includes all the key features we discussed:
Key Features

Three-state workflow: Setup → Practice → Review
Chinese language support: Characters and Pinyin representation
Audio playback: Text-to-speech for pronunciation practice
Image upload: For submitting handwritten Chinese characters
OCR integration: Using EasyOCR for character recognition
Detailed feedback: Character-by-character comparison
Grading system: S-A-B-C-D ranking with color coding

How to Run the App

Save the code to a file named app.py
Install the required dependencies:
Copypip install streamlit pillow gtts easyocr numpy pandas

Run the app with:
Copystreamlit run app.py


Implementation Notes

The app includes mock data and functions since we don't have access to actual APIs
For a production version, you would replace:

The mock word collection with actual API calls
The hardcoded sentences with LLM-generated content
The simplified grading with more advanced OCR and LLM assessment



The application has a clean, user-friendly interface with proper styling and state management. It demonstrates the complete workflow while maintaining all the educational features required for effective language learning.

Claude 3 Haiku Integration

Added AWS configuration:

AWS credentials input in the sidebar (hidden by default)
Region selection dropdown
Secure password input for credentials


Bedrock client setup:

Added boto3 integration for Amazon Bedrock
Created a function to call Claude 3 Haiku specifically
Set up appropriate error handling for API calls


LLM-powered functions:

Sentence generation: Now uses Claude 3 Haiku to create Chinese sentences based on vocabulary words
Grading and feedback: Uses Claude to analyze handwritten submissions and provide educational feedback



Cost-Saving Measures

Cached results:

Used Streamlit's caching to prevent redundant API calls
Implemented fallback mechanisms if API calls fail


Optimized prompts:

Short, focused prompts to minimize token usage
Low temperature settings (0.1-0.3) for more deterministic responses
Structured JSON outputs to reduce parsing complexity


Efficient Claude usage:

Only using Claude for high-value tasks (sentence generation and grading)
Keeping local processing for simpler tasks



How to Run the App

Save the code to a file named app.py
Install the required dependencies:
Copypip install streamlit pillow gtts easyocr numpy pandas boto3

Set up your AWS credentials:

You can enter them directly in the app's sidebar
Or set them as environment variables before running


Run the app with:
Copystreamlit run app.py


This implementation balances cost efficiency with functionality, making it ideal for a bootcamp project where both learning and budget are priorities. The Claude 3 Haiku model is Amazon Bedrock's most cost-effective option while still providing high-quality language capabilities for your Putonghua learning app.



Writing Practice

Difficulty: Level 200

Business Goal: 
Students have asked if there could be a learning exercise to practice writing language sentences.
You have been tasked to build a prototyping application which will take a word group, and generate very simple sentences in english, and you must write them in the target lanagueg eg. Japanese.


Technical Requirements:
Streamlit
MangaOCR (Japanese) or for another language use Managed LLM that has Vision eg. GPT4o
Be able to upload an image





Kana Practice Apps (Hard Requirement)
Use a Vision Encoder Decoder for your target language. Eg. Toki Pona, Japanese, Chinese.
Be able to input your image either webcam, upload or draw
Decide on what you want to evaluate:
Sentence
Word
Character


Technical Uncertainties and Suggestions:
Vision Encoder Decoder Integration:

Uncertainty: Integrating a Vision Encoder Decoder model for recognizing characters in various languages (e.g., Toki Pona, Japanese, Chinese).
Suggestion: Use pre-trained models like Tesseract OCR for initial testing and then fine-tune a Vision Transformer (ViT) model for better accuracy in recognizing specific characters.
Image Input Handling:

Uncertainty: Allowing users to input images via webcam, upload, or drawing.
Suggestion: Implement a multi-input system using libraries like OpenCV for webcam capture, Streamlit for file uploads, and a drawing canvas using HTML5 Canvas or a library like Fabric.js.
Evaluation Criteria:

Uncertainty: Deciding what to evaluate (sentence, word, character).
Suggestion: Start with character recognition to build a robust foundation, then expand to word and sentence evaluation. Use a modular approach to easily add new evaluation criteria.
Language-Specific Challenges:

Uncertainty: Handling the nuances of different languages (e.g., stroke order in Japanese, tonal differences in Chinese).
Suggestion: Incorporate language-specific preprocessing steps, such as stroke order verification for Japanese or tone detection for Chinese, using specialized libraries or custom algorithms.
User Interface and Experience:

Uncertainty: Designing an intuitive and user-friendly interface.
Suggestion: Use a framework like Streamlit for rapid prototyping and gather user feedback to iteratively improve the UI. Ensure the interface supports all input methods seamlessly.
Performance and Scalability:

Uncertainty: Ensuring the app performs well with various input types and scales efficiently.
Suggestion: Optimize the Vision Encoder Decoder model for speed and accuracy, and use cloud services like AWS or Google Cloud for scalable backend processing.


For a project focused on Putonghua (Mandarin Chinese), you have several OCR (Optical Character Recognition) options to consider:

Tesseract OCR: This is a popular open-source OCR engine that supports Chinese Simplified characters. It's highly customizable and can be integrated into your Python projects easily.

Google Cloud Vision OCR: This service offers robust OCR capabilities, including support for Chinese Simplified. It's a paid service but provides high accuracy and additional features like handwriting recognition.

MyFreeOCR: This is a free online tool that supports Chinese Simplified OCR. It can convert scanned documents or images into text documents1.

PDF24 OCR: This online tool allows you to recognize text in PDF files and create searchable PDFs. It supports multiple languages, including Chinese Simplified2.

olmOCR: An open-source tool designed for high-throughput conversion of PDFs and other documents into plain text. It supports various document types and is known for its accurac


