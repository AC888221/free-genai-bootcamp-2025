# Listening Comp: Language Learning Assistant (LLA)
This is for the generative AI bootcamp

[Jump to Bootcamp Week 2: LLA Implementation Report](https://github.com/AC888221/free-genai-bootcamp-2025/blob/main/language-learning-assistant-main/README.md#bootcamp-week-2-lla-implementation-report)

## Overview
The Listening Comp project is designed to enhance language learning through the integration of generative AI and various AWS services. This application focuses on providing a structured approach to language learning, utilizing Retrieval-Augmented Generation (RAG) techniques to ground responses in real lesson content.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technical Details](#technical-details)

## Features
- **Interactive Learning**: Offers practice scenarios to enhance user engagement.

## Installation
To set up the project, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/listening-comp.git
   cd listening-comp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
To run the main application, execute the following command:

Make sure to have your AWS credentials configured properly to access the necessary services.

## Technical Details
- **Frameworks and Libraries**: The application utilizes Streamlit for the user interface, along with various AWS services for backend processing.
- **Database**: Faiss is used for vector storage, ensuring efficient data retrieval and management.
- **APIs**: The application integrates with the YouTube Transcript API for handling video transcripts.

### Technical Uncertainties

**Q:** How did I address the unavailability of Amazon Nova models in AWS regions near Australia?
**A:** I discovered that Amazon Nova models are not available in the Asia Pacific (Sydney) or Asia Pacific (Melbourne) regions. To overcome this, I selected the US West (Oregon) region [us-west-2] as the nearest alternative to manage latency and performance considerations.

**Q:** How did I locate HSK2 practice tests on YouTube with Putonghua subtitles?
**A:** While I was able to filter Youtube videos based on whether subtitles were enabled, it seemed many HSK2 test videos did not have subtitles and those that did usually had subtitltes in languages other than Putonghua. However, I did find one channel that seemed to have a lot (https://www.youtube.com/@mengziyu396).

**Q:** Many HSK2 practice tests on YouTube seem not to have Chinese subtitles. How did I try to work around this issue?
**A:** I used the YouTube API to implement translation of other subtitles, such as English, into Chinese using the googletrans library, which is a Python wrapper for the Google Translate API.

**Q:** How did I overcome the compatibility issues between the googletrans library and chromadb due to dependency conflict?
**A:** I resolved the compatibility issues by switching from googletrans to faiss. The googletrans library and chromadb were reliant on different versions of httpx. By using faiss, I avoided these conflicts and maintained the necessary functionality for my project.

**Q:** How did I overcome the limitation of having only one female Chinese voice for Amazon Polly?
**A:** I used FFmpeg's capabilities to modify the pitch, rate, and volume of the generated audio files, creating variations that simulate different voices. This allowed me to create two reasonably distinctive female voices despite the limitation.

## Bootcamp Week 2: LLA Implementation Report

## Domain Knowledge Acquired Through Technical Uncertainty
Throughout the development of the Language Listening App, several technical uncertainties were encountered and overcome, leading to valuable domain knowledge in various areas:

### Pulling Transcriptions from YouTube
- **API Integration**: Successfully integrated the YouTube Transcript API to pull transcriptions, managing API responses, rate limits, and implementing robust error handling using the `YouTubeTranscriptDownloader` class.
- **Multilingual Support**: Handled transcripts in multiple languages (Simplified Chinese and English), managing language codes and ensuring accurate translations with the help of the Google Translate API.

### Formatting Data for Vector Store
- **Vector Storage and Retrieval**: Utilized FAISS for efficient vector storage and similarity search, embedding questions and managing embeddings for quick information retrieval with functions like `embed_questions` and `save_embeddings`.
- **Data Validation and Cleaning**: Ensured data cleanliness and validity by removing duplicates and handling empty lines, using the `HSK2TranscriptProcessor` class.

### Fetching Similar Questions Based on Inputted Topic
- **Session Management**: Maintained user sessions in Streamlit to ensure state across different stages of the application, ensuring a smooth user experience.
- **Conditional Logic for File Processing**: Identified and listed text files that did not have corresponding audio files, ensuring the app could both play existing audio files and process new ones.

### Generating a Question in the Frontend UI
- **User Interface Design**: Designed an intuitive user interface using Streamlit, creating clear navigation, input fields, and user-friendly result displays with functions like `render_header` and `render_sidebar`.
- **Streamlit App Structure**: Understood the importance of function calls within a Streamlit app to render specific stages based on user interaction, using a main function to conditionally render different parts of the app.

### Generating Audio for Students to Listen
- **Audio Processing**: Implemented audio generation using Amazon Polly, managing audio files, handling formats, and verifying audio integrity with the `process_text_files` function.
- **Audio Processing Integration**: Used the subprocess module to run external scripts (e.g., `tts.py`) from within a Streamlit app, handling potential errors during subprocess execution and providing user feedback.

### Interactive Learning
- **Embedding and Similarity Search**: Utilized FAISS and cosine similarity to find the top similar embeddings for a given query, ensuring relevant context retrieval.
- **Response Generation**: Used Amazon Bedrock to generate responses based on user input and retrieved contexts, integrating with the `BedrockChat` class.
- **Handling NaN Values**: Implemented a method to replace NaN values in embeddings with the mean of non-NaN values or a default value, ensuring robust data handling.

### Text Processing
- **Context Retrieval**: Loaded embeddings and included HSK2 data, ensuring relevant context retrieval for user queries.
- **Response Generation**: Generated responses using Amazon Bedrock based on user input and retrieved contexts, integrating with the `BedrockChat` class.
- **Similarity Search**: Found the top similar embeddings for a given query using cosine similarity, ensuring relevant context retrieval.

### Text-to-Speech
- **Audio Generation**: Used Amazon Polly to generate audio from text, managing pitch, rate, and volume settings to create natural-sounding speech.
- **Error Handling**: Implemented robust error handling and retries for audio generation, ensuring reliable performance.
- **Audio File Management**: Managed audio files effectively, verifying their integrity and format using `pydub` and `filetype`.
- **Audio Concatenation**: Combined multiple audio files into a single file using FFmpeg, ensuring correct format and minimal loss during concatenation.

### Additional Technical Knowledge
- **Logging and Debugging**: Implemented logging to facilitate debugging and monitoring, tracking application behavior and identifying issues in real-time.
- **File and Directory Management**: Set up and verified the existence of directories, creating them if they didn't exist, and listed files in directories based on file extensions.
- **AWS Services Integration**: Used Amazon Polly for text-to-speech conversion and Amazon Bedrock for text analysis and speaker identification with the `BedrockChat` class.
- **Token Management**: Managed token limits for input and output in the Bedrock model, adjusting token limits to account for prompt overhead.
- **FFmpeg Usage**: Concatenated multiple audio files into a single file using FFmpeg, handling file paths and ensuring the correct format for FFmpeg input.
- **String Manipulation**: Extracted and modified parts of filenames to generate new file names, removing specific prefixes and extensions.
- **Context Management**: Used context managers to handle file operations safely and efficiently.
- **Directory Path Management**: Used absolute paths to avoid issues with relative paths, constructing absolute paths using `os.path.abspath`.
- **Error Handling and Logging**: Implemented error handling for missing directories, logging warnings and errors to track issues.
- **Streamlit Application Development**: Set up and rendered different stages in a Streamlit app, using components like `st.header`, `st.selectbox`, `st.audio`, and `st.button`.
- **Interactive Audio Processing**: Set up an interface for selecting and playing audio files, triggering audio processing with a button and handling the processing logic.
- **Debugging and Troubleshooting**: Identified and resolved issues related to incorrect file paths, ensuring proper indentation and formatting in Python scripts.

