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