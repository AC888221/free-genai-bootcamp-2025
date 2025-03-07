# Putonghua Language Learning App

A Streamlit-based application for practicing Chinese (Putonghua) writing with AI-powered feedback using Claude 3 Haiku.

## Overview

This application helps users practice Chinese writing through a three-stage workflow:
1. **Setup**: Configure AWS credentials and settings
2. **Practice**: Generate and study Chinese sentences
3. **Review**: Submit and receive feedback on handwritten characters

## Features

- **Three-stage Learning Workflow**
- **Chinese Language Support**: Characters and Pinyin representation
- **Audio Playback**: Text-to-speech for pronunciation practice
- **Flexible Image Upload**: Traditional upload or WSL file path support
- **OCR Integration**: Using EasyOCR for character recognition
- **AI-Powered Feedback**: Character-by-character analysis using Claude 3 Haiku
- **Comprehensive Grading**: A-F ranking with detailed feedback

## Project Structure

```
writing-practice/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration settings
├── frontend/
│   ├── styling.py        # CSS and UI styling
│   └── state_management.py # Session state management
├── backend/
│   ├── ocr_reader.py     # OCR initialization
│   ├── bedrock_client.py # AWS Bedrock setup
│   ├── claude_haiku.py   # Claude API integration
│   ├── word_collection.py # Vocabulary management
│   ├── sentence_generation.py # Sentence creation
│   ├── audio_generation.py # Text-to-speech
│   └── image_processing.py # Image analysis
├── requirements.txt      # Python dependencies
└── .gitignore           # Git ignore rules
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/writing-practice.git
cd writing-practice
```

2. Create and activate a virtual environment:
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Set up AWS credentials either:
   - Through the application's sidebar
   - Via environment variables:
     ```bash
     export AWS_ACCESS_KEY_ID='your_access_key'
     export AWS_SECRET_ACCESS_KEY='your_secret_key'
     export AWS_DEFAULT_REGION='your_region'
     ```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Navigate through the three stages:
   - Configure settings in Setup
   - Generate and practice sentences
   - Submit writing for review and feedback

### Image Upload Options

The app supports two methods for submitting handwritten work:
1. **Traditional File Upload**: Standard file browser (for most users)
2. **WSL File Path**: Direct path input for Windows Subsystem for Linux users

## Grading Criteria

### Grading Scale
- **A (Excellent)**: Perfect stroke order, accurate formation
- **B (Good)**: Minor mistakes, mostly accurate
- **C (Average)**: Noticeable errors but recognizable
- **D (Needs Improvement)**: Significant formation issues
- **F (Fail)**: Unrecognizable characters

### Evaluation Aspects
- Stroke Order
- Character Accuracy
- Completeness
- Neatness

## Technical Requirements

- Python 3.8+
- Streamlit
- EasyOCR
- AWS Bedrock access
- PIL (Python Imaging Library)
- boto3

## Development Notes

- Uses mock data for development; replace with actual APIs in production
- Implements caching for cost optimization
- Structured for easy expansion and modification

