# Putonghua Language Learning App

A Streamlit-based application for practicing Chinese (Putonghua) writing with AI-powered feedback using Claude 3 Haiku.

[Jump to Bootcamp Week 2: Writing Practice Implementation Report](https://github.com/yourusername/writing-practice/blob/main/README.md#bootcamp-week-2-writing-practice-implementation-report)

## Overview

This application helps users practice Chinese writing through a three-stage workflow:
1. **Setup**: Configure AWS credentials and settings
2. **Practice**: Generate and study Chinese sentences with audio support
3. **Review**: Submit and receive feedback on handwritten characters through image processing

## Features

- **Three-stage Learning Workflow**
- **Chinese Language Support**: Characters and Pinyin representation
- **Audio Support**: 
  - Text-to-speech conversion using gTTS (Google Text-to-Speech)
  - Pronunciation practice for Chinese characters and sentences
- **Image Processing**:
  - Character recognition using Tesseract OCR
  - Support for handwritten character submissions
  - Image preprocessing and enhancement using Pillow
- **AI-Powered Feedback**: Character-by-character analysis using Claude 3 Haiku

## System Requirements

### Required System Dependencies

1. **Tesseract OCR** - Required for character recognition
   
   For Ubuntu/Debian:
   ```bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   sudo apt-get install tesseract-ocr-chi-sim  # For Chinese support
   ```
   
   For Windows:
   1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
   2. Run the installer
   3. Add Tesseract to your PATH environment variable
   
   For macOS:
   ```bash
   brew install tesseract
   brew install tesseract-lang  # For language support
   ```

   Verify installation:
   ```bash
   tesseract --version
   ```

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

1. Install system dependencies (see System Requirements above)

2. Clone the repository:
```bash
git clone https://github.com/yourusername/writing-practice.git
cd writing-practice
```

3. Create and activate a virtual environment:
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Set up AWS credentials via environment variables:
```bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_DEFAULT_REGION='your_region'
```

2. Verify Tesseract installation:
```bash
tesseract --version
```

3. Navigate through the three stages:
   - Configure settings in Setup
   - Generate and practice sentences with audio support
   - Submit handwritten characters for review and feedback

### Image Upload Options

The app supports two methods for submitting handwritten work:
1. **Traditional File Upload**: Standard file browser (for most users)
2. **WSL File Path**: Direct path input for Windows Subsystem for Linux users

## Technical Requirements

- Python 3.8+
- Tesseract OCR with Chinese language support
- Core Dependencies:
  - numpy==1.26.0
  - pandas==2.1.1
  - streamlit==1.27.0
  - pytesseract==0.3.13
- API Dependencies:
  - flask==2.3.3
  - flask-cors==4.0.0
- Image Processing:
  - Pillow==9.5.0
- Audio Processing:
  - gtts==2.3.2
- AWS Integration:
  - boto3==1.28.62
  - botocore>=1.31.62

## Troubleshooting

### Common Issues

1. **OCR Not Working**
   - Verify Tesseract is installed: `tesseract --version`
   - Check Chinese language support: `tesseract --list-langs`
   - Ensure image is clear and well-lit

2. **Image Processing Errors**
   - Confirm image format is supported (PNG, JPEG, BMP)
   - Check image resolution and size
   - Ensure proper lighting and contrast in handwriting

### Getting Help

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify all system requirements are met
3. Ensure all dependencies are properly installed

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

## Known Limitations

- Tesseract OCR works best with clear, well-formatted handwriting
- Audio generation requires an active internet connection
- Some features may require specific browser permissions (microphone, file system)

## Bootcamp Week 2: Writing Practice Implementation Report

## Domain Knowledge Acquired Through Technical Uncertainty

Throughout the development of the Writing Practice App, several technical uncertainties were encountered and overcome, leading to valuable domain knowledge in various areas:

### Chinese Character Recognition and OCR
- **Tesseract Integration**: Successfully integrated Tesseract OCR with Chinese language support, managing character recognition accuracy and implementing robust error handling.
- **Image Preprocessing**: Developed expertise in image enhancement techniques using Pillow to improve OCR accuracy for handwritten Chinese characters.
- **Multi-platform Support**: Handled Tesseract installation and configuration across different operating systems (Windows, macOS, Linux/WSL).

### Text-to-Speech Implementation
- **gTTS Integration**: Successfully implemented Google Text-to-Speech for Chinese language support, managing API responses and audio file generation.
- **Audio File Management**: Developed systems for generating, storing, and serving audio files efficiently within the Streamlit application.
- **Error Handling**: Implemented robust retry mechanisms for audio generation failures and network connectivity issues.

### Streamlit Application Architecture
- **State Management**: Implemented efficient session state management for handling the three-stage workflow (Setup, Practice, Review).
- **UI/UX Design**: Created an intuitive interface for character practice and submission, with clear navigation between stages.
- **File Upload Handling**: Developed flexible file upload solutions supporting both traditional uploads and WSL file paths.

### Chinese Language Processing
- **Character Analysis**: Implemented systems for analyzing Chinese character structure and stroke order.
- **Pinyin Generation**: Managed the complexity of displaying both Chinese characters and their Pinyin representations.
- **Grading System**: Developed a comprehensive grading framework for evaluating character writing accuracy.

### AI Integration
- **Claude Integration**: Successfully integrated Claude 3 Haiku for providing detailed feedback on character writing.
- **Prompt Engineering**: Developed effective prompts for generating appropriate practice sentences and detailed writing feedback.
- **Response Processing**: Implemented parsing and formatting of AI responses for clear feedback presentation.

### Image Processing Pipeline
- **Format Handling**: Developed support for multiple image formats (PNG, JPEG, BMP) with appropriate validation.
- **Preprocessing Workflow**: Created an image preprocessing pipeline to optimize character recognition:
  - Contrast enhancement
  - Noise reduction
  - Size normalization
  - Format standardization

### Error Handling and Validation
- **Input Validation**: Implemented comprehensive validation for image uploads and file formats.
- **OCR Quality Checks**: Developed methods to verify OCR output quality and reliability.
- **Graceful Degradation**: Implemented fallback mechanisms for various failure scenarios.

### System Integration
- **AWS Integration**: Successfully configured and managed AWS services for cloud-based processing.
- **API Management**: Developed structured approaches to handling multiple API integrations (AWS, Google TTS).
- **Cross-platform Compatibility**: Ensured consistent functionality across different operating systems and environments.

### Performance Optimization
- **Caching Strategy**: Implemented efficient caching for API responses and processed images.
- **Resource Management**: Optimized memory usage for image processing and OCR operations.
- **Response Time**: Improved application responsiveness through strategic use of async operations.

